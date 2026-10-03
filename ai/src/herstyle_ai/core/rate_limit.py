"""Small process-local rate limiter used as a safe baseline.

For multiple workers/replicas, keep the endpoint limits at the edge or replace
this store with Redis. The API still refuses unbounded bursts when deployed as
one process.
"""

from collections import defaultdict
from threading import Lock
import time


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._buckets: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def check(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        now = time.monotonic()
        cutoff = now - window_seconds
        with self._lock:
            bucket = [timestamp for timestamp in self._buckets[key] if timestamp > cutoff]
            if len(bucket) >= limit:
                retry_after = max(1, int(window_seconds - (now - bucket[0])))
                self._buckets[key] = bucket
                return False, retry_after
            bucket.append(now)
            self._buckets[key] = bucket
            return True, 0


rate_limiter = InMemoryRateLimiter()


__all__ = ["InMemoryRateLimiter", "rate_limiter"]
