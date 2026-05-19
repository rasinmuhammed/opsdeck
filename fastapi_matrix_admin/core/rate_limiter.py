import time
from typing import Dict, Tuple


class RateLimiter:
    """
    Simple in-memory rate limiter using Token Bucket algorithm.
    Suitable for single-instance deployments.
    For horizontal scaling, this should be replaced with Redis.
    """

    def __init__(self, rate: int, per: int):
        self.rate = rate
        self.per = per
        self.buckets: Dict[str, Tuple[float, float]] = (
            {}
        )  # key -> (tokens, last_update)

    def accumulate(self, key: str):
        now = time.time()
        tokens, last_update = self.buckets.get(key, (self.rate, now))

        # Calculate new tokens
        elapsed = now - last_update
        new_tokens = elapsed * (self.rate / self.per)
        tokens = min(self.rate, tokens + new_tokens)

        return tokens, now

    def check(self, key: str) -> bool:
        """Check if request is allowed without consuming tokens."""
        tokens, _ = self.accumulate(key)
        return tokens >= 1.0

    def consume(self, key: str) -> bool:
        """Consume a token if available."""
        tokens, now = self.accumulate(key)

        if tokens >= 1.0:
            self.buckets[key] = (tokens - 1.0, now)
            return True
        else:
            # Update timestamp even if failed to prevent stale data
            self.buckets[key] = (tokens, now)
            return False
