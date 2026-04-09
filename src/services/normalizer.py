"""
Data normalizer for the Job Aggregator.

Converts raw API/scraper-specific payloads into the unified job schema
that the database layer expects. Every source has its own raw format;
this module absorbs all those differences.

Usage
-----
    from src.services.normalizer import normalize_job

    normalised = normalize_job(raw_dict, source="remoteok")
"""

import re
from datetime import datetime, timezone
from typing import Any

from src.core.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Unified schema
# ---------------------------------------------------------------------------

_UNIFIED_FIELDS = (
    "external_id",
    "source",
    "title",
    "company",
    "location",
    "description",
    "url",
    "tags",
    "posted_at",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_str(value: Any, default: str = "") -> str:
    """
    Coerce *value* to a stripped string, returning *default* on None / empty.
    """
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _clean_html(html: str) -> str:
    """Strip HTML tags and normalise whitespace."""
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&#\d+;", " ", text)
    text = re.sub(r"&[a-z]+;", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _parse_epoch(value: Any) -> str:
    """
    Convert a UNIX timestamp (int or string) to an ISO-8601 datetime string.
    Returns an empty string if conversion fails.
    """
    if not value:
        return ""
    try:
        ts = int(value)
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return dt.isoformat()
    except (ValueError, TypeError, OSError):
        return ""


def _normalise_tags(value: Any) -> list[str]:
    """
    Normalise a tags field into a list of non-empty lowercase strings.

    Accepts: list, comma-separated string, or None.
    """
    if not value:
        return []
    if isinstance(value, list):
        return [t.strip().lower() for t in value if str(t).strip()]
    if isinstance(value, str):
        return [t.strip().lower() for t in value.split(",") if t.strip()]
    return []


# ---------------------------------------------------------------------------
# Source-specific raw → normalised mappers
# ---------------------------------------------------------------------------

def _map_remoteok(raw: dict[str, Any]) -> dict[str, Any]:
    """Map a single RemoteOK API item to the unified schema."""
    return {
        "external_id": _clean_str(raw.get("id") or raw.get("slug"), default="unknown"),
        "source": "remoteok",
        "title": _clean_str(raw.get("position")),
        "company": _clean_str(raw.get("company")),
        "location": _clean_str(raw.get("location"), default="Remote"),
        "description": _clean_html(raw.get("description", "")),
        "url": _clean_str(raw.get("url") or raw.get("apply_url")),
        "tags": _normalise_tags(raw.get("tags")),
        "posted_at": _parse_epoch(raw.get("epoch") or raw.get("date")),
    }


def _map_arbeitnow(raw: dict[str, Any]) -> dict[str, Any]:
    """Map a single Arbeitnow API item to the unified schema."""
    return {
        "external_id": _clean_str(raw.get("slug"), default="unknown"),
        "source": "arbeitnow",
        "title": _clean_str(raw.get("title")),
        "company": _clean_str(raw.get("company_name")),
        "location": _clean_str(raw.get("location"), default="Remote"),
        "description": _clean_html(raw.get("description", "")),
        "url": _clean_str(raw.get("url")),
        "tags": _normalise_tags(raw.get("tags")),
        "posted_at": _clean_str(raw.get("created_at")),
    }


def _map_hackernews(raw: dict[str, Any]) -> dict[str, Any]:
    """Map a single HackerNews Firebase item to the unified schema."""
    return {
        "external_id": _clean_str(raw.get("id"), default="unknown"),
        "source": "hackernews",
        "title": _clean_str(raw.get("title")),
        "company": _clean_str(raw.get("by")),    # poster username as company
        "location": "Remote",
        "description": _clean_html(raw.get("text", "")),
        "url": _clean_str(raw.get("url")),
        "tags": [],
        "posted_at": _parse_epoch(raw.get("time")),
    }


def _map_weworkremotely(raw: dict[str, Any]) -> dict[str, Any]:
    """Map a scraped WeWorkRemotely listing to the unified schema."""
    return {
        "external_id": _clean_str(raw.get("external_id"), default="unknown"),
        "source": "weworkremotely",
        "title": _clean_str(raw.get("title")),
        "company": _clean_str(raw.get("company")),
        "location": _clean_str(raw.get("location"), default="Remote"),
        "description": "",   # listing pages do not provide full description
        "url": _clean_str(raw.get("url")),
        "tags": _normalise_tags(raw.get("tags")),
        "posted_at": _clean_str(raw.get("posted_at")),
    }


_MAPPERS = {
    "remoteok": _map_remoteok,
    "arbeitnow": _map_arbeitnow,
    "hackernews": _map_hackernews,
    "weworkremotely": _map_weworkremotely,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def normalize_job(raw: dict[str, Any], source: str) -> dict[str, Any] | None:
    """
    Convert a raw source-specific job dict into the unified schema.

    Parameters
    ----------
    raw    : Raw dict as returned by the API client or scraper.
    source : Source identifier string — one of 'remoteok', 'arbeitnow',
             'hackernews', 'weworkremotely'.

    Returns
    -------
    dict
        Normalised job with all unified schema fields present, or None if
        the raw item could not be mapped (missing title + external_id).
    """
    mapper = _MAPPERS.get(source)
    if mapper is None:
        logger.warning("normalize_job: unknown source %r — skipping", source)
        return None

    try:
        normalised = mapper(raw)
    except Exception as exc:
        logger.error("normalize_job: mapper raised for source=%r: %s", source, exc)
        return None

    # Reject records that have no usable identity.
    if not normalised.get("title") and not normalised.get("external_id"):
        logger.debug("normalize_job: discarding empty record from %r", source)
        return None

    return normalised


def normalize_jobs(
    raws: list[dict[str, Any]],
    source: str,
) -> list[dict[str, Any]]:
    """
    Normalise a list of raw job dicts from the same source.

    Silently drops items that fail normalisation.

    Returns
    -------
    list[dict]  — only successfully normalised records.
    """
    results = []
    for raw in raws:
        normalised = normalize_job(raw, source)
        if normalised is not None:
            results.append(normalised)

    logger.info(
        "normalize_jobs: %d/%d records normalised from source=%r",
        len(results),
        len(raws),
        source,
    )
    return results
