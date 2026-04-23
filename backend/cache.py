# cache.py
# Responsibility: In-memory cache for query results.
# Key = MD5 hash of the query string (lowercased, stripped).
# Value = the full response dict.

import hashlib
import time
import config


class QueryCache:
    def __init__(self, max_size: int = config.CACHE_MAX_SIZE):
        self._store: dict[str, dict] = {}
        self._timestamps: dict[str, float] = {}
        self.max_size  = max_size
        self.hits      = 0
        self.misses    = 0

    def _key(self, query: str) -> str:
        """Normalize query and hash it."""
        normalized = query.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()

    def get(self, query: str) -> dict | None:
        """Return cached result or None."""
        key = self._key(query)
        if key in self._store:
            self.hits += 1
            result = dict(self._store[key])
            result["cache_hit"] = True
            return result
        self.misses += 1
        return None

    def set(self, query: str, result: dict):
        """Store a result. Evict oldest entry if cache is full."""
        if len(self._store) >= self.max_size:
            # Evict the oldest entry (FIFO)
            oldest_key = min(self._timestamps, key=self._timestamps.get)
            del self._store[oldest_key]
            del self._timestamps[oldest_key]

        key = self._key(query)
        self._store[key]      = result
        self._timestamps[key] = time.time()

    def stats(self) -> dict:
        total = self.hits + self.misses
        return {
            "cached_queries": len(self._store),
            "hits":           self.hits,
            "misses":         self.misses,
            "hit_rate":       round(self.hits / total, 3) if total > 0 else 0
        }


# Global singleton
_cache = QueryCache()

def get_cache() -> QueryCache:
    return _cache