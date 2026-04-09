"""
HackerNews Firebase API client for the Job Aggregator.

Endpoints:
  - https://hacker-news.firebaseio.com/v0/jobstories.json (Index)
  - https://hacker-news.firebaseio.com/v0/item/{id}.json (Item Details)

Budget: EXACTLY 4 requests per run (1 index + 3 items).
Auth  : None.

Usage
-----
    from src.core.rate_limiter import RateLimiter
    from src.api_clients.hackernews import fetch_jobs

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

_SOURCE = "hackernews"


# ---------------------------------------------------------------------------
# Internal request helper
# ---------------------------------------------------------------------------

def _make_request(url: str, limiter: RateLimiter) -> requests.Response:
    """
    Perform a single GET request to the specified URL, respecting rate-limiter guards.

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
            url,
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
        raise CriticalHTTPError(response.status_code, url)

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
                url,
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
    Fetch job listings from HackerNews Firebase API.

    Makes 1 request for the top job stories index, then fetches details for
    up to `config.HACKERNEWS_MAX_ITEMS` IDs individually. Max 4 requests total.
    
    Parameters
    ----------
    limiter : Shared RateLimiter instance for this aggregation run.

    Returns
    -------
    list[dict]
        Raw job dicts ready for the normalizer. Returns whatever was successfully
        fetched so far if an individual request fails unrecoverably.
    """
    logger.info("[%s] Starting fetch (budget remaining: %d)", _SOURCE, limiter.remaining_budget())

    # 1) Fetch index
    try:
        response = _make_request(config.HACKERNEWS_JOBSTORIES_URL, limiter)
    except CriticalHTTPError:
        raise
    except (RateLimitExhausted, RuntimeLimitExceeded):
        raise
    except Exception as exc:
        logger.error("[%s] Unrecoverable error fetching job stories index: %s", _SOURCE, exc)
        return []

    try:
        story_ids = response.json()
    except ValueError as exc:
        logger.error("[%s] Failed to parse job stories JSON response: %s", _SOURCE, exc)
        return []

    if not isinstance(story_ids, list):
        logger.error("[%s] Unexpected index response type — expected list, got %s", _SOURCE, type(story_ids).__name__)
        return []

    if not story_ids:
        logger.warning("[%s] Job stories index returned empty", _SOURCE)
        return []

    # Limit IDs to config bound (e.g. 3 items)
    target_ids = story_ids[:config.HACKERNEWS_MAX_ITEMS]
    logger.info("[%s] Job stories index fetched. Proceeding to fetch %d items.", _SOURCE, len(target_ids))

    # 2) Fetch individual items
    jobs = []
    for item_id in target_ids:
        item_url = config.HACKERNEWS_ITEM_URL.format(item_id=item_id)
        try:
            item_response = _make_request(item_url, limiter)
            item_data = item_response.json()
            if isinstance(item_data, dict):
                jobs.append(item_data)
        except CriticalHTTPError:
            raise
        except (RateLimitExhausted, RuntimeLimitExceeded):
            raise
        except Exception as exc:
            # Retry failed -> stop THAT SOURCE, do not retry other items
            logger.error("[%s] Unrecoverable error fetching item %s: %s. Stopping source.", _SOURCE, item_id, exc)
            break

    logger.info("[%s] Fetched %d raw job records", _SOURCE, len(jobs))
    return jobs
