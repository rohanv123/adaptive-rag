# adaptive.py
# Responsibility: Analyze query → decide top_K and strategy.
# Also maintain running state updated by the feedback loop.

import time
import config


class AdaptiveState:
    """
    Holds the live system state that changes as queries come in.
    One instance lives for the lifetime of the server.
    """
    def __init__(self):
        self.avg_latency_ms  = 300.0    # starts optimistic
        self.current_k       = config.DEFAULT_TOP_K
        self.strategy        = "hybrid"
        self.total_queries   = 0
        self.low_quality_streak = 0   # consecutive low-quality answers
        self.query_history   = []     # list of recent decisions for logging

    def update_latency(self, latency_ms: float):
        """
        Update the rolling average latency using Exponential Moving Average.
        EMA reacts faster to recent data than a simple mean.
        """
        self.avg_latency_ms = (
            config.EMA_ALPHA * latency_ms +
            (1 - config.EMA_ALPHA) * self.avg_latency_ms
        )

    def get_status(self) -> dict:
        return {
            "avg_latency_ms":    round(self.avg_latency_ms, 1),
            "current_k":         self.current_k,
            "strategy":          self.strategy,
            "total_queries":     self.total_queries,
            "low_quality_streak": self.low_quality_streak
        }


# Global singleton — one shared state for the entire server process
_state = AdaptiveState()


def score_complexity(query: str) -> dict:
    """
    Analyze a query and return a complexity score + features.

    Complexity factors:
    - Word count (longer = more complex)
    - Presence of analytical/comparison keywords
    - Presence of multi-part indicators ("and", "also", "compare")
    - Question word type (why/how = harder than what/who)
    """
    words      = query.strip().split()
    word_count = len(words)
    query_lower = query.lower()

    # Score starts at 0, add points for each complexity signal
    score = 0

    # Length signals
    if word_count >= config.COMPLEX_QUERY_WORDS:
        score += 3
    elif word_count >= 10:
        score += 2
    elif word_count >= 6:
        score += 1

    # Analytical keywords → need more context
    analytical_words = {
        "explain", "describe", "compare", "difference", "contrast",
        "why", "how", "advantages", "disadvantages", "tradeoffs",
        "analyze", "evaluate", "relationship", "between", "versus"
    }
    hit_count = sum(1 for w in words if w in analytical_words)
    score += min(hit_count, 3)   # cap contribution at 3

    # Multi-part indicators → might need more chunks
    multi_part_words = {"and", "also", "additionally", "furthermore", "both"}
    if any(w in query_lower for w in multi_part_words):
        score += 1

    # Very short queries are often keyword lookups
    is_lookup = word_count <= config.SHORT_QUERY_WORDS

    return {
        "score":      score,
        "word_count": word_count,
        "is_lookup":  is_lookup,
        "hit_words":  hit_count
    }


def decide(query: str) -> dict:
    """
    The core adaptive function.
    Given a query, decide top_k and retrieval strategy.
    Also consider current system latency state.

    Returns a dict with: top_k, strategy, complexity, reason
    """
    complexity = score_complexity(query)
    c_score    = complexity["score"]
    latency_ok = _state.avg_latency_ms < config.HIGH_LATENCY_MS

    # ── Decide top_k ──────────────────────────────────────────────
    if not latency_ok:
        # System under pressure → minimize retrieval depth
        top_k  = config.MIN_TOP_K
        reason = "latency pressure → reduced K"

    elif c_score >= 5:
        # Very complex query → needs lots of context
        top_k  = min(config.MAX_TOP_K, config.DEFAULT_TOP_K + 3)
        reason = "high complexity → large K"

    elif c_score >= 3:
        # Moderately complex
        top_k  = config.DEFAULT_TOP_K
        reason = "moderate complexity → default K"

    elif complexity["is_lookup"]:
        # Short lookup query → small K, fast
        top_k  = config.MIN_TOP_K + 1
        reason = "short lookup query → small K"

    else:
        top_k  = config.DEFAULT_TOP_K
        reason = "standard query → default K"

    # ── Decide strategy ───────────────────────────────────────────
    if complexity["is_lookup"]:
        # Short queries → keyword search wins (exact term matching)
        strategy = "keyword"
    elif c_score >= 4 or complexity["word_count"] >= 15:
        # Long/complex queries → semantic search wins
        strategy = "vector"
    else:
        # Middle ground → hybrid is best
        strategy = "hybrid"

    # Clamp top_k to valid range
    top_k = max(config.MIN_TOP_K, min(config.MAX_TOP_K, top_k))

    # Record this decision
    _state.total_queries += 1
    _state.current_k      = top_k
    _state.strategy       = strategy
    _state.query_history.append({
        "query":      query[:80],   # store first 80 chars only
        "top_k":      top_k,
        "strategy":   strategy,
        "complexity": c_score,
        "reason":     reason,
        "ts":         time.time()
    })

    # Keep only last 50 decisions in memory
    if len(_state.query_history) > 50:
        _state.query_history.pop(0)

    return {
        "top_k":      top_k,
        "strategy":   strategy,
        "complexity": c_score,
        "word_count": complexity["word_count"],
        "reason":     reason
    }


def feedback_update(latency_ms: float, quality_proxy: float,
                    user_rating: int | None = None):
    """
    Called after each query completes. Updates the state.

    quality_proxy: a 0–1 score computed from answer length and rating.
    user_rating: explicit 1–5 stars from the user (optional).

    Logic:
    - If quality is consistently low AND latency allows → increase K
    - If latency is consistently high → decrease K  
    - If user rates poorly 3+ times in a row → force hybrid strategy
    """
    _state.update_latency(latency_ms)

    # Track low-quality streak
    if quality_proxy < 0.35:
        _state.low_quality_streak += 1
    else:
        _state.low_quality_streak = 0

    # If stuck in low quality and system is fast enough → try bigger K
    if (
        _state.low_quality_streak >= 3
        and _state.avg_latency_ms < 600
        and _state.current_k < config.MAX_TOP_K
    ):
        _state.current_k += 1

    # If system too slow → reduce K
    if (
        _state.avg_latency_ms > config.HIGH_LATENCY_MS * 1.2
        and _state.current_k > config.MIN_TOP_K
    ):
        _state.current_k -= 1

    # Explicit user rating overrides
    if user_rating is not None:
        if user_rating <= 2 and _state.strategy != "hybrid":
            _state.strategy = "hybrid"   # bad rating → try hybrid


def get_state() -> AdaptiveState:
    """Expose the global state to other modules."""
    return _state