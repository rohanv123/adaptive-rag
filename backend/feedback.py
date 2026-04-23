# feedback.py
# Responsibility: Log every interaction to disk (JSONL format).
# JSONL = one JSON object per line. Easy to analyze later.

import json
import time
from pathlib import Path

LOG_FILE = "interactions.jsonl"


def compute_quality_proxy(answer: str, user_rating: int | None = None) -> float:
    """
    Estimate answer quality without a trained model.

    Heuristics:
    - Length: longer answers are usually more complete (up to a point)
    - No error markers: "I don't have enough" = low quality
    - User rating (if provided) dominates

    Returns a 0.0 – 1.0 score.
    """
    if user_rating is not None:
        # Map 1-5 stars to 0.0-1.0
        return (user_rating - 1) / 4.0

    answer_words = len(answer.split())

    # Error/refusal → low quality
    if "i don't have enough" in answer.lower():
        return 0.1
    if "error" in answer.lower()[:50]:
        return 0.05

    # Length heuristic: 20-150 words = good range
    if answer_words < 10:
        length_score = 0.2
    elif answer_words < 20:
        length_score = 0.4
    elif answer_words <= 150:
        length_score = 0.8 + (answer_words / 150) * 0.2
    else:
        length_score = 0.9   # very long answers might be padded

    return min(length_score, 1.0)


def log_interaction(query: str, answer: str, latency_ms: float,
                    retrieval_ms: float, generation_ms: float,
                    top_k: int, strategy: str,
                    user_rating: int | None = None) -> dict:
    """Write one interaction record to the JSONL log file."""
    quality = compute_quality_proxy(answer, user_rating)

    record = {
        "timestamp":      time.time(),
        "query":          query,
        "answer_preview": answer[:200],   # don't store full answer in log
        "latency_ms":     round(latency_ms, 1),
        "retrieval_ms":   round(retrieval_ms, 1),
        "generation_ms":  round(generation_ms, 1),
        "top_k":          top_k,
        "strategy":       strategy,
        "answer_words":   len(answer.split()),
        "quality_proxy":  round(quality, 3),
        "user_rating":    user_rating
    }

    # Append to JSONL file
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    return record


def load_recent_interactions(n: int = 20) -> list[dict]:
    """Load the last n interactions from the log file."""
    if not Path(LOG_FILE).exists():
        return []
    lines = Path(LOG_FILE).read_text().strip().split("\n")
    recent = lines[-n:]
    return [json.loads(line) for line in recent if line.strip()]