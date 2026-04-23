# reranker.py
# Responsibility: Re-score retrieved candidates using a cross-encoder.
# Cross-encoders are more accurate than bi-encoders but slower,
# so we only use them on a small set of pre-retrieved candidates.

from sentence_transformers import CrossEncoder
import config

print("Loading cross-encoder model...")
# ms-marco = trained on Microsoft MARCO passage ranking dataset
# MiniLM = small and fast, good for production
_cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
print("Cross-encoder loaded.")


def rerank(query: str, candidates: list[dict]) -> list[dict]:
    """
    Score each (query, chunk) pair with the cross-encoder.
    Returns candidates sorted by cross-encoder score (highest first).

    The cross-encoder outputs a relevance score (not a probability).
    Higher = more relevant. The scale doesn't matter — only the ranking.
    """
    if not candidates:
        return []

    # Build (query, document_text) pairs for the cross-encoder
    pairs = [(query, c["text"]) for c in candidates]

    # Predict relevance scores for all pairs
    # This is the expensive step — O(N) forward passes through the model
    scores = _cross_encoder.predict(pairs)

    # Attach scores to each candidate
    for candidate, score in zip(candidates, scores):
        candidate["rerank_score"] = float(score)

    # Sort by rerank_score descending
    candidates.sort(key=lambda x: -x["rerank_score"])
    return candidates