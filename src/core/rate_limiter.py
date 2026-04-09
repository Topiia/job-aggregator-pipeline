"""
Rate limiter for the Job Aggregator system.

Enforces global request limits, inter-request delays, and runtime
timeouts across all API clients and scrapers. A single RateLimiter
instance is created per aggregation run and shared with every source.

Usage:
    from src.core.rate_limiter import RateLimiter

    limiter = RateLimiter()

    if not limiter.can_request():
        raise RateLimitExhausted("Request budget exhausted")

    limiter.wait()            # sleep 4-6 seconds
    response = requests.get(url, headers=config.HEADERS)
    limiter.record_request()  # increment counter
"""

import random
import time
import logging

from src.core.config import config


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class RateLimitExhausted(Exception):
    """Raised when the global request budget has been exhausted."""


class RuntimeLimitExceeded(Exception):
    """Raised when the total runtime limit has been exceeded."""


class CriticalHTTPError(Exception):
    """Raised on HTTP 429 or 403 — triggers immediate global stop."""

    def __init__(self, status_code: int, url: str):
        self.status_code = status_code
        self.url = url
        super().__init__(
            f"Critical HTTP {status_code} received from {url} — stopping all sources"
        )


# ---------------------------------------------------------------------------
# RateLimiter
# ---------------------------------------------------------------------------

class RateLimiter:
    """
    Controls request pacing, counting, and runtime enforcement.

    Thread-safety is NOT required — the aggregator runs sequentially.
    """

    def __init__(self) -> None:
        self._request_count: int = 0
        self._start_time: float = time.time()
        self._max_requests: int = config.MAX_REQUESTS_PER_RUN
        self._delay_range: tuple = config.DELAY_BETWEEN_REQUESTS
        self._runtime_limit: int = config.TOTAL_RUNTIME_LIMIT

    # ----- Query methods --------------------------------------------------

    def can_request(self) -> bool:
        """Return True if the request budget has not been exhausted."""
        return self._request_count < self._max_requests

    def remaining_budget(self) -> int:
        """Return how many requests remain before hitting the cap."""
        remaining = self._max_requests - self._request_count
        return max(remaining, 0)

    def check_timeout(self) -> bool:
        """Return True if TOTAL_RUNTIME_LIMIT has been exceeded."""
        elapsed = time.time() - self._start_time
        return elapsed > self._runtime_limit

    @property
    def request_count(self) -> int:
        """Total number of requests recorded so far."""
        return self._request_count

    @property
    def elapsed_time(self) -> float:
        """Seconds elapsed since this limiter was created."""
        return time.time() - self._start_time

    # ----- Action methods -------------------------------------------------

    def wait(self) -> None:
        """
        Sleep for a randomized duration between DELAY_BETWEEN_REQUESTS bounds.

        This MUST be called before every HTTP request to space them out
        and avoid detection patterns.
        """
        delay = random.uniform(self._delay_range[0], self._delay_range[1])
        logger.debug(
            "Rate limiter: sleeping %.2fs (request %d/%d, elapsed %.1fs)",
            delay,
            self._request_count + 1,
            self._max_requests,
            self.elapsed_time,
        )
        time.sleep(delay)

    def record_request(self) -> None:
        """Increment the global request counter by one."""
        self._request_count += 1
        logger.info(
            "Request %d/%d recorded (%.1fs elapsed, %d remaining)",
            self._request_count,
            self._max_requests,
            self.elapsed_time,
            self.remaining_budget(),
        )

    # ----- Guard methods --------------------------------------------------

    def enforce_budget(self) -> None:
        """
        Raise RateLimitExhausted if the request budget is exhausted.

        Call this at the top of every fetch function, before wait().
        """
        if not self.can_request():
            raise RateLimitExhausted(
                f"Request budget exhausted: {self._request_count}/{self._max_requests} "
                f"requests used in {self.elapsed_time:.1f}s"
            )

    def enforce_timeout(self) -> None:
        """
        Raise RuntimeLimitExceeded if the total runtime limit is exceeded.

        Call this at the top of the aggregator loop before each source.
        """
        if self.check_timeout():
            raise RuntimeLimitExceeded(
                f"Runtime limit exceeded: {self.elapsed_time:.1f}s > "
                f"{self._runtime_limit}s limit after {self._request_count} requests"
            )

    def pre_request_check(self) -> None:
        """
        Combined guard: enforce timeout, then budget, then wait.

        Convenience method that API clients call before every HTTP request:

            rate_limiter.pre_request_check()
            response = requests.get(url, headers=config.HEADERS)
            rate_limiter.record_request()
        """
        self.enforce_timeout()
        self.enforce_budget()
        self.wait()
