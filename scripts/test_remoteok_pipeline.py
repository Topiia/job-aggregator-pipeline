"""
End-to-end pipeline test: RemoteOK → normalize → SQLite.

Run from the project root:
    python scripts/test_remoteok_pipeline.py

This script:
  1. Initialises the database (creates tables if absent).
  2. Creates a RateLimiter instance.
  3. Fetches jobs from the RemoteOK API (exactly 1 request).
  4. Normalises the raw response into the unified schema.
  5. Upserts normalised jobs into SQLite.
  6. Prints a summary: total fetched, normalised, inserted.

Safety guarantees:
  - RateLimiter prevents > MAX_REQUESTS_PER_RUN requests.
  - CriticalHTTPError (429/403) stops execution immediately.
  - Any other failure returns an empty list and prints an error.
"""

import sys
import os

# Ensure the project root is on sys.path when run as a script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.logger import get_logger
from src.core.rate_limiter import CriticalHTTPError, RateLimiter
from src.db.database import init_db
from src.db.operations import get_job_stats, upsert_jobs
from src.api_clients.remoteok import fetch_jobs
from src.services.normalizer import normalize_jobs

logger = get_logger(__name__)


def run_pipeline() -> None:
    print("=" * 60)
    print("  RemoteOK Pipeline — End-to-End Test")
    print("=" * 60)

    # ── Step 1: Initialise database ──────────────────────────────────
    print("\n[1/5] Initialising database...")
    init_db()
    print("      Database ready.")

    # ── Step 2: Create rate limiter ──────────────────────────────────
    print("\n[2/5] Creating RateLimiter...")
    limiter = RateLimiter()
    print(f"      Budget: {limiter.remaining_budget()} requests available.")

    # ── Step 3: Fetch from RemoteOK ──────────────────────────────────
    print("\n[3/5] Fetching jobs from RemoteOK API...")
    print("      (sleeping 4–6 seconds as per rate-limit policy)")
    try:
        raw_jobs = fetch_jobs(limiter)
    except CriticalHTTPError as exc:
        print(f"\n[!] CRITICAL HTTP {exc.status_code} — pipeline stopped.")
        print(f"    URL: {exc.url}")
        sys.exit(1)
    except Exception as exc:
        print(f"\n[!] Unexpected error during fetch: {exc}")
        sys.exit(1)

    print(f"      Fetched {len(raw_jobs)} raw records.")
    print(f"      Requests used: {limiter.request_count}/{limiter.remaining_budget() + limiter.request_count}")

    if not raw_jobs:
        print("\n[!] No jobs returned from API. Nothing to store.")
        return

    # ── Step 4: Normalise ────────────────────────────────────────────
    print("\n[4/5] Normalising records...")
    normalised = normalize_jobs(raw_jobs, source="remoteok")
    print(f"      Normalised {len(normalised)}/{len(raw_jobs)} records successfully.")

    if not normalised:
        print("\n[!] All records failed normalisation. Nothing to store.")
        return

    # Sample — show first 3 titles to confirm data looks sane.
    print("\n      Sample (first 3 jobs):")
    for job in normalised[:3]:
        title = job.get("title") or "(no title)"
        company = job.get("company") or "(no company)"
        tags = ", ".join(job.get("tags", [])[:4]) or "—"
        print(f"      • {title} @ {company}  [{tags}]")

    # ── Step 5: Persist to database ──────────────────────────────────
    print("\n[5/5] Inserting into database...")
    inserted = upsert_jobs(normalised)
    skipped = len(normalised) - inserted

    # ── Summary ──────────────────────────────────────────────────────
    stats = get_job_stats()
    print("\n" + "=" * 60)
    print("  Pipeline Complete")
    print("=" * 60)
    print(f"  Raw fetched    : {len(raw_jobs)}")
    print(f"  Normalised     : {len(normalised)}")
    print(f"  Inserted (new) : {inserted}")
    print(f"  Skipped (dupe) : {skipped}")
    print(f"  Total in DB    : {stats['total']}")
    print(f"  By source      : {stats['by_source']}")
    print(f"  Requests used  : {limiter.request_count}")
    print(f"  Elapsed time   : {limiter.elapsed_time:.1f}s")
    print("=" * 60)


if __name__ == "__main__":
    run_pipeline()
