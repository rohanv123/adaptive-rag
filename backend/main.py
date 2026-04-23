# main.py
# The FastAPI application.
# Run with: uvicorn main:app --reload --port 8000

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import time

from ingestion    import load_raw_documents, chunk_documents
from vector_store import build_index, load_index
from retriever    import build_bm25, hybrid_search
from reranker     import rerank
from adaptive     import decide, feedback_update, get_state
from generator    import generate
from feedback     import log_interaction, load_recent_interactions, compute_quality_proxy
from metrics      import Timer, get_tracker
from cache        import get_cache

# ➤ Added import
from decomposer import should_decompose, decompose


# ── Global objects (built at startup) ────────────────────────────
faiss_index = None
bm25_index  = None
all_chunks  = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Code here runs ONCE when the server starts.
    We build the index here so API requests can use it immediately.
    """
    global faiss_index, bm25_index, all_chunks

    print("=" * 50)
    print("Starting Adaptive RAG server...")
    print("=" * 50)

    # Try loading saved index first (faster restart)
    saved = load_index()
    if saved:
        faiss_index, all_chunks = saved
        print("Loaded existing index from disk.")
    else:
        # Build fresh index from documents
        print("Building index from documents...")
        docs        = load_raw_documents()
        all_chunks  = chunk_documents(docs)
        if not all_chunks:
            print("WARNING: No documents found. Add .txt or .pdf to data/documents/")
            all_chunks = [{"text": "No documents loaded.", "source": "none", "chunk_id": "none_0"}]
        faiss_index, _, all_chunks = build_index(all_chunks)

    # Build BM25 index (always rebuild — it's fast)
    bm25_index = build_bm25(all_chunks)

    print(f"Server ready. {len(all_chunks)} chunks indexed.")
    print("=" * 50)

    yield   # ← server runs here

    print("Server shutting down.")


# ── Create the app ────────────────────────────────────────────────
app = FastAPI(
    title="Adaptive RAG API",
    version="1.0.0",
    lifespan=lifespan
)

# Allow requests from React dev server (localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request/Response models ───────────────────────────────────────
class QueryRequest(BaseModel):
    query: str

class FeedbackRequest(BaseModel):
    query:  str
    rating: int   # 1–5 stars


# ── Endpoints ─────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "Adaptive RAG API is running.", "docs": "/docs"}


@app.post("/query")
def query_endpoint(req: QueryRequest):
    """
    Main endpoint. Accepts a query, runs the full RAG pipeline,
    returns answer + metadata for the UI dashboard.
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # 1. Check cache first
    cache = get_cache()
    query_clean = req.query.strip().lower()
    cached = cache.get(query_clean)
    if cached:
        return cached

    with Timer() as total_timer:

        # 2. Adaptive decision
        decision = decide(req.query)
        top_k    = decision["top_k"]
        strategy = decision["strategy"]

        # 3. Hybrid retrieval (UPDATED BLOCK)
        with Timer() as ret_timer:
            if should_decompose(req.query):
                sub_queries = decompose(req.query)
                all_candidates = []

                for sq in sub_queries:
                    sub_results = hybrid_search(
                        sq, faiss_index, bm25_index, all_chunks,
                        top_k=max(3, top_k // len(sub_queries)),
                        strategy=strategy
                    )
                    all_candidates.extend(sub_results)

                # Deduplicate by chunk_id
                seen = {}
                for c in all_candidates:
                    if c["chunk_id"] not in seen:
                        seen[c["chunk_id"]] = c

                candidates = list(seen.values())[:top_k * 2]
            else:
                candidates = hybrid_search(
                    req.query, faiss_index, bm25_index, all_chunks,
                    top_k=top_k, strategy=strategy
                )

            ranked = rerank(req.query, candidates)

        retrieval_ms = ret_timer.ms

        # 4. LLM generation (timed separately)
        with Timer() as gen_timer:
            context_chunks = ranked[:top_k]
            llm_result     = generate(req.query, context_chunks)

        generation_ms = gen_timer.ms
        answer        = llm_result["answer"]

    total_ms = total_timer.ms

    # 5. Update metrics
    tracker = get_tracker()
    tracker.record(total_ms, retrieval_ms, generation_ms, top_k, strategy)

    # 6. Update adaptive state with latency feedback
    quality = compute_quality_proxy(answer)
    feedback_update(total_ms, quality)

    # 7. Log interaction
    log_interaction(
        req.query, answer, total_ms, retrieval_ms,
        generation_ms, top_k, strategy
    )

    # 8. Build response
    response = {
        "answer":  answer,
        "sources": [
            {"file": c["source"], "preview": c["text"][:120] + "..."}
            for c in context_chunks
        ],
        "meta": {
            "top_k":          top_k,
            "strategy":       strategy,
            "complexity":     decision["complexity"],
            "reason":         decision["reason"],
            "retrieval_ms":   round(retrieval_ms, 1),
            "generation_ms":  round(generation_ms, 1),
            "total_ms":       round(total_ms, 1),
            "cache_hit":      False,
            "chunks_indexed": len(all_chunks),
            # ➤ Added meta fields
            "decomposed": should_decompose(req.query),
            "sub_queries": decompose(req.query) if should_decompose(req.query) else []
        }
    }

    # 9. Store in cache for future identical queries
    cache.set(req.query, response)
    return response


@app.post("/feedback")
def feedback_endpoint(req: FeedbackRequest):
    """Receive explicit user rating (1–5) for a query."""
    if not 1 <= req.rating <= 5:
        raise HTTPException(status_code=400, detail="Rating must be 1–5")

    state = get_state()
    feedback_update(
        latency_ms=state.avg_latency_ms,
        quality_proxy=(req.rating - 1) / 4.0,
        user_rating=req.rating
    )
    # Re-log with rating
    log_interaction(req.query, "", state.avg_latency_ms,
                    0, 0, state.current_k, state.strategy, req.rating)
    return {"status": "ok", "new_k": state.current_k}


@app.get("/metrics")
def metrics_endpoint():
    """Full latency and performance statistics."""
    tracker = get_tracker()
    cache   = get_cache()
    state   = get_state()

    return {
        **tracker.report(),
        "cache":          cache.stats(),
        "adaptive_state": state.get_status(),
        "recent_logs":    load_recent_interactions(10)
    }


@app.get("/health")
def health():
    """Simple health check."""
    return {
        "status": "ok",
        "chunks": len(all_chunks),
        "model":  "all-MiniLM-L6-v2"
    }


@app.post("/reindex")
def reindex():
    """Rebuild the index from documents. Call after adding new documents."""
    global faiss_index, bm25_index, all_chunks
    docs       = load_raw_documents()
    all_chunks = chunk_documents(docs)
    faiss_index, _, all_chunks = build_index(all_chunks)
    bm25_index = build_bm25(all_chunks)
    return {"status": "ok", "chunks": len(all_chunks)}
