"""
RemoteOK API client for the Job Aggregator.

Endpoint : https://remoteok.com/api
Budget   : EXACTLY 1 request per run (enforced by RateLimiter).
Auth     : None.

The API returns a JSON array whose FIRST element is metadata — it must
be discarded. Every subsequent element is a job listing.

Usage
-----
    from src.core.rate_limiter import RateLimiter
    from src.api_clients.remoteok import fetch_jobs

    limiter = RateLimiter()
    jobs = fetch_jobs(limiter)
"""

import time
import random

import requests

from src.core.config import config
from src.core.logger import get_logger
from src.core.rate_limiter import (
    CriticalHTTPError,
    RateLimiter,
    RateLimitExhausted,
    RuntimeLimitExceeded,
)

logger = get_logger(__name__)

_SOURCE = "remoteok"
_URL = config.REMOTEOK_URL

# Hard cap on jobs returned by this client.
# Applied after parsing, before the list is handed to the normalizer.
_MAX_JOBS = 50


# ---------------------------------------------------------------------------
# Internal request helper
# ---------------------------------------------------------------------------

def _make_request(limiter: RateLimiter) -> requests.Response:
    """
    Perform a single GET request, respecting rate-limiter guards.

    Raises
    ------
    RateLimitExhausted   : Budget exhausted before this request could be made.
    RuntimeLimitExceeded : Total runtime limit exceeded.
    CriticalHTTPError    : HTTP 429 or 403 received.
    requests.RequestException : Network-level failure (after 1 retry).
    """
    # Guard: timeout and budget both checked before attempting the request.
    limiter.pre_request_check()

    try:
        response = requests.get(
            _URL,
            headers=config.HEADERS,
            timeout=config.REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        logger.error("[%s] Network error on first attempt: %s", _SOURCE, exc)
        raise

    # Record the request regardless of response status.
    limiter.record_request()

    # Handle critical HTTP errors — stop immediately, no retry.
    if response.status_code in (429, 403):
        logger.error(
            "[%s] Critical HTTP %d received — stopping immediately",
            _SOURCE,
            response.status_code,
        )
        raise CriticalHTTPError(response.status_code, _URL)

    # Handle server errors — one retry with backoff.
    if response.status_code >= 500:
        retry_delay = random.uniform(
            config.RETRY_DELAY[0], config.RETRY_DELAY[1]
        )
        logger.warning(
            "[%s] HTTP %d — retrying once after %.1fs",
            _SOURCE,
            response.status_code,
            retry_delay,
        )
        time.sleep(retry_delay)

        # One retry — checks budget again before the second attempt.
        limiter.pre_request_check()
        try:
            response = requests.get(
                _URL,
                headers=config.HEADERS,
                timeout=config.REQUEST_TIMEOUT,
            )
        except requests.RequestException as exc:
            logger.error("[%s] Network error on retry: %s", _SOURCE, exc)
            raise
        limiter.record_request()

        if response.status_code != 200:
            logger.error(
                "[%s] Retry also failed with HTTP %d — stopping this source",
                _SOURCE,
                response.status_code,
            )
            response.raise_for_status()

    response.raise_for_status()
    return response


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fetch_jobs(limiter: RateLimiter) -> list[dict]:
    """
    Fetch job listings from the RemoteOK API.

    Exactly 1 HTTP request is made (2 on server error + retry).
    The first element of the response array (metadata) is discarded.

    Parameters
    ----------
    limiter : Shared RateLimiter instance for this aggregation run.

    Returns
    -------
    list[dict]
        Raw job dicts ready for the normalizer. Returns empty list on
        any unrecoverable failure so the aggregator can continue.
    """
    logger.info("[%s] Starting fetch (budget remaining: %d)", _SOURCE, limiter.remaining_budget())

    try:
        response = _make_request(limiter)
    except CriticalHTTPError:
        raise   # propagate — aggregator must stop all sources
    except (RateLimitExhausted, RuntimeLimitExceeded):
        raise   # propagate — aggregator must stop all sources
    except Exception as exc:
        logger.error("[%s] Unrecoverable error during fetch: %s", _SOURCE, exc)
        return []

    # Parse JSON safely.
    try:
        data = response.json()
    except ValueError as exc:
        logger.error("[%s] Failed to parse JSON response: %s", _SOURCE, exc)
        return []

    if not isinstance(data, list):
        logger.error(
            "[%s] Unexpected response type — expected list, got %s",
            _SOURCE,
            type(data).__name__,
        )
        return []

    if not data:
        logger.warning("[%s] API returned an empty array", _SOURCE)
        return []

    # First element is always API metadata — skip it.
    jobs = data[1:]
    raw_count = len(jobs)

    # Enforce hard volume cap: fetch → parse → LIMIT → normalise → store.
    if raw_count > _MAX_JOBS:
        jobs = jobs[:_MAX_JOBS]
        logger.info(
            "[%s] Fetched %d jobs, limited to %d for controlled processing",
            _SOURCE,
            raw_count,
            _MAX_JOBS,
        )
    else:
        logger.info("[%s] Fetched %d raw job records", _SOURCE, raw_count)

    return jobs
