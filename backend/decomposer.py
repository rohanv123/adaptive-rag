# decomposer.py
# If a query contains "and", "compare X with Y", or "also",
# split it into sub-queries, retrieve for each, merge results.

import re

def should_decompose(query: str) -> bool:
    """Detect multi-part queries."""
    triggers = [
        r"\band\b.*\band\b",        # "X and Y and Z"
        r"\bcompare\b.*\bwith\b",   # "compare X with Y"
        r"\bversus\b|\bvs\b",       # "X vs Y"
        r"\bdifference between\b",  # "difference between X and Y"
        r"\bboth\b.*\band\b",       # "both X and Y"
    ]
    return any(re.search(p, query.lower()) for p in triggers)

def decompose(query: str) -> list[str]:
    """Split a complex query into simpler sub-queries."""
    q = query.strip()

    # "compare X with Y" → ["What is X?", "What is Y?"]
    m = re.search(r"compare (.+?) (?:with|vs|versus|and) (.+)", q, re.I)
    if m:
        return [
            f"What is {m.group(1).strip()}?",
            f"What is {m.group(2).strip()}?",
            q   # also keep original for context
        ]

    # "X and Y" split at "and"
    parts = re.split(r"\band\b", q, flags=re.I)
    if len(parts) >= 2:
        return [p.strip() for p in parts if len(p.strip()) > 5]

    return [q]  # no decomposition needed