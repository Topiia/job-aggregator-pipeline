"""
Arbeitnow API client for the Job Aggregator.

Endpoint : https://www.arbeitnow.com/api/job-board-api
Budget   : EXACTLY 1 request per run (enforced by RateLimiter).
Auth     : None.

The API returns a JSON object where the 'data' key contains an array of
job listings. Pagination is intentionally ignored to adhere to the
1 request boundary.

Usage
-----
    from src.core.rate_limiter import RateLimiter
    from src.api_clients.arbeitnow import fetch_jobs

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

_SOURCE = "arbeitnow"
_URL = config.ARBEITNOW_URL

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

    limiter.record_request()

    if response.status_code in (429, 403):
        logger.error(
            "[%s] Critical HTTP %d received — stopping immediately",
            _SOURCE,
            response.status_code,
        )
        raise CriticalHTTPError(response.status_code, _URL)

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
    Fetch job listings from the Arbeitnow API (page 1 only).

    Exactly 1 HTTP request is made (2 on server error + retry).
    
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

    try:
        data = response.json()
    except ValueError as exc:
        logger.error("[%s] Failed to parse JSON response: %s", _SOURCE, exc)
        return []

    if not isinstance(data, dict) or "data" not in data:
        logger.error(
            "[%s] Unexpected response structure — expected dict with 'data' array",
            _SOURCE,
        )
        return []

    jobs = data["data"]
    if not isinstance(jobs, list):
        logger.error("[%s] 'data' key is not a list", _SOURCE)
        return []

    if not jobs:
        logger.warning("[%s] API returned an empty list of jobs", _SOURCE)
        return []

    raw_count = len(jobs)
    if raw_count > _MAX_JOBS:
        jobs = jobs[:_MAX_JOBS]
        logger.info(
            "[%s] Fetched %d jobs, limited to %d for controlled processing",
            _SOURCE,
            raw_count,
            len(jobs),
        )
    else:
        logger.info("[%s] Fetched %d raw job records", _SOURCE, raw_count)

    return jobs
