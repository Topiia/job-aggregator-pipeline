"""
Central configuration for the Job Aggregator system.

All execution limits, per-source budgets, HTTP headers, and paths
are defined here as a single source of truth. Every module imports
from this file — no module defines its own constants.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Tuple


# ---------------------------------------------------------------------------
# Project root is two levels up from this file:
#   src/core/config.py  →  job_aggregator/
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass(frozen=True)
class Config:
    """Immutable, type-safe application configuration."""

    # ------------------------------------------------------------------
    # Global execution constraints
    # ------------------------------------------------------------------
    MAX_REQUESTS_PER_RUN: int = 15
    DELAY_BETWEEN_REQUESTS: Tuple[int, int] = (4, 6)
    TOTAL_RUNTIME_LIMIT: int = 90  # seconds
    RUN_FREQUENCY: str = "daily"
    RUN_TIME: str = "11:50"  # IST
    MAX_RETRIES: int = 1
    RETRY_DELAY: Tuple[int, int] = (8, 10)

    # ------------------------------------------------------------------
    # Per-source request budgets
    # ------------------------------------------------------------------
    REMOTEOK_MAX_REQUESTS: int = 1
    ARBEITNOW_MAX_REQUESTS: int = 1
    HACKERNEWS_MAX_ITEMS: int = 3
    WWR_MAX_PAGES: int = 2
    WWR_MAX_JOBS: int = 50

    # ------------------------------------------------------------------
    # API / Scraper URLs
    # ------------------------------------------------------------------
    REMOTEOK_URL: str = "https://remoteok.com/api"
    ARBEITNOW_URL: str = "https://www.arbeitnow.com/api/job-board-api"
    HACKERNEWS_JOBSTORIES_URL: str = (
        "https://hacker-news.firebaseio.com/v0/jobstories.json"
    )
    HACKERNEWS_ITEM_URL: str = (
        "https://hacker-news.firebaseio.com/v0/item/{item_id}.json"
    )
    WWR_URL: str = (
        "https://weworkremotely.com/categories/remote-programming-jobs"
    )

    # ------------------------------------------------------------------
    # Global HTTP headers — used by every client and scraper
    # ------------------------------------------------------------------
    HEADERS: Dict[str, str] = field(default_factory=lambda: {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/html",
        "Accept-Language": "en-US,en;q=0.9",
    })

    # ------------------------------------------------------------------
    # Paths
    # ------------------------------------------------------------------
    DB_PATH: str = field(
        default_factory=lambda: str(_PROJECT_ROOT / "data" / "jobs.db")
    )
    LOG_PATH: str = field(
        default_factory=lambda: str(_PROJECT_ROOT / "logs" / "logs.txt")
    )
    DATA_PATH: str = field(
        default_factory=lambda: str(_PROJECT_ROOT / "data")
    )
    LAST_RUN_PATH: str = field(
        default_factory=lambda: str(_PROJECT_ROOT / "data" / "last_run.json")
    )

    # ------------------------------------------------------------------
    # HTTP timeout for individual requests (seconds)
    # ------------------------------------------------------------------
    REQUEST_TIMEOUT: int = 15


# ---------------------------------------------------------------------------
# Module-level singleton — import this everywhere:
#
#   from src.core.config import config
# ---------------------------------------------------------------------------
config = Config()
