# vector_store.py
# Responsibility: Build a FAISS index from chunks, and search it.

import numpy as np
import faiss
import pickle
from pathlib import Path
from sentence_transformers import SentenceTransformer
import config

# Load the embedding model once when this file is first imported.
# SentenceTransformer downloads the model on first use (~90MB).
print(f"Loading embedding model: {config.EMBED_MODEL}")
_embed_model = SentenceTransformer(config.EMBED_MODEL)
print("Embedding model loaded.")

INDEX_FILE  = "faiss_index.pkl"   # saved index file
CHUNKS_FILE = "chunks.pkl"        # saved chunks file


def embed_texts(texts: list[str]) -> np.ndarray:
    """
    Convert a list of strings into a 2D numpy array of shape (N, 384).
    normalize_embeddings=True makes each vector unit length,
    so inner product == cosine similarity. This is important for IndexFlatIP.
    """
    return _embed_model.encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True,
        batch_size=32   # process 32 chunks at a time to save memory
    )


def build_index(chunks: list[dict]) -> tuple:
    """
    Build a FAISS IndexFlatIP from all chunks.
    Returns (faiss_index, numpy_embeddings, chunks_list)

    IndexFlatIP = Flat index using Inner Product (= cosine similarity
    when vectors are normalized). 'Flat' means exact search — no
    approximation. Correct for small/medium datasets (<100k chunks).
    For very large datasets, use IndexIVFFlat (approximate, faster).
    """
    texts      = [c["text"] for c in chunks]
    embeddings = embed_texts(texts)

    dimension = embeddings.shape[1]   # 384 for all-MiniLM-L6-v2
    index     = faiss.IndexFlatIP(dimension)
    index.add(embeddings.astype(np.float32))

    print(f"FAISS index built: {index.ntotal} vectors, dimension={dimension}")

    # Save to disk so we don't rebuild on every restart
    with open(INDEX_FILE, "wb")  as f: pickle.dump(index, f)
    with open(CHUNKS_FILE, "wb") as f: pickle.dump(chunks, f)

    return index, embeddings, chunks


def load_index() -> tuple | None:
    """Try to load saved index from disk. Returns None if not found."""
    if Path(INDEX_FILE).exists() and Path(CHUNKS_FILE).exists():
        print("Loading FAISS index from disk...")
        with open(INDEX_FILE,  "rb") as f: index  = pickle.load(f)
        with open(CHUNKS_FILE, "rb") as f: chunks = pickle.load(f)
        print(f"Loaded index with {index.ntotal} vectors.")
        return index, chunks
    return None


def vector_search(query: str, index, chunks: list[dict],
                  top_k: int = config.DEFAULT_TOP_K) -> list[dict]:
    """
    Embed the query and find the top_k most similar chunks.
    Returns a list of chunk dicts, each with an added 'vector_score' key.
    """
    # Embed the query (must be normalized same as the index vectors)
    q_emb = _embed_model.encode(
        [query], normalize_embeddings=True
    ).astype(np.float32)

    # FAISS search: returns (scores, indices)
    # scores[0] = similarity scores for the top hits
    # indices[0] = which chunk (by position) those hits came from
    scores, indices = index.search(q_emb, top_k)

    results = []
    for rank, (idx, score) in enumerate(zip(indices[0], scores[0])):
        if idx == -1:
            continue  # FAISS returns -1 when fewer results exist than top_k
        result = dict(chunks[idx])          # copy chunk dict
        result["vector_score"] = float(score)
        result["rank_vector"]  = rank
        results.append(result)

    return results