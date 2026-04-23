# retriever.py
# Responsibility: Keyword search with BM25 + hybrid merge logic.

from rank_bm25 import BM25Okapi
import config


def build_bm25(chunks: list[dict]) -> BM25Okapi:
    """
    Build a BM25 index from all chunk texts.
    BM25Okapi is the standard variant — uses Okapi BM25 formula.

    We tokenize by lowercasing and splitting on spaces.
    Simple but effective for most cases.
    """
    tokenized_corpus = [c["text"].lower().split() for c in chunks]
    bm25 = BM25Okapi(tokenized_corpus)
    print(f"BM25 index built over {len(chunks)} chunks.")
    return bm25


def keyword_search(query: str, bm25: BM25Okapi,
                   chunks: list[dict],
                   top_k: int = config.DEFAULT_TOP_K) -> list[dict]:
    """
    Score all chunks using BM25 and return top_k results.
    """
    query_tokens = query.lower().split()
    scores       = bm25.get_scores(query_tokens)
    # argsort gives indices in ascending order; [::-1] reverses to descending
    top_indices  = scores.argsort()[::-1][:top_k]

    results = []
    for rank, idx in enumerate(top_indices):
        if scores[idx] < 0.001:
            continue   # skip chunks with near-zero BM25 score
        result = dict(chunks[idx])
        result["bm25_score"] = float(scores[idx])
        result["rank_bm25"]  = rank
        results.append(result)

    return results


def hybrid_search(query: str, index, bm25: BM25Okapi,
                  chunks: list[dict],
                  top_k: int = config.DEFAULT_TOP_K,
                  strategy: str = "hybrid") -> list[dict]:
    """
    Combine vector search and BM25 keyword search.

    Strategy selection:
    - "vector"  → only semantic search
    - "keyword" → only BM25
    - "hybrid"  → both, merged by Reciprocal Rank Fusion

    Reciprocal Rank Fusion (RRF):
    RRF is a way to merge two ranked lists without knowing their score scales.
    Score for a chunk = 1/(rank_in_list_A + 60) + 1/(rank_in_list_B + 60)
    The 60 is a smoothing constant that prevents top-ranked items from
    dominating too much. Chunks appearing high in BOTH lists score highest.
    """
    from vector_store import vector_search

    if strategy == "vector":
        return vector_search(query, index, chunks, top_k)

    if strategy == "keyword":
        return keyword_search(query, bm25, chunks, top_k)

    # --- HYBRID: fetch more candidates then fuse ---
    fetch_k = min(top_k * 3, len(chunks))  # fetch 3x more to merge well

    vec_results = vector_search(query, index, chunks, fetch_k)
    kw_results  = keyword_search(query, bm25, chunks, fetch_k)

    # Build rank maps: chunk_id → rank in each list
    vec_ranks = {r["chunk_id"]: i for i, r in enumerate(vec_results)}
    kw_ranks  = {r["chunk_id"]: i for i, r in enumerate(kw_results)}

    # Merge all unique chunks from both results
    all_chunks_map = {}
    for r in vec_results + kw_results:
        all_chunks_map[r["chunk_id"]] = r

    # Compute RRF score for each chunk
    K = 60   # RRF smoothing constant
    scored = []
    for cid, chunk in all_chunks_map.items():
        rrf_score = 0.0
        if cid in vec_ranks:
            rrf_score += 1.0 / (vec_ranks[cid] + K)
        if cid in kw_ranks:
            rrf_score += 1.0 / (kw_ranks[cid] + K)
        chunk["rrf_score"] = rrf_score
        scored.append(chunk)

    # Sort by RRF score descending, take top_k
    scored.sort(key=lambda x: -x["rrf_score"])
    return scored[:top_k]