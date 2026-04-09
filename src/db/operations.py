"""
Database CRUD operations for the Job Aggregator.

All operations receive normalised job dicts and persist them to SQLite via
SQLAlchemy. Deduplication is handled at the DB level using the UNIQUE
constraint on (source, external_id).

Usage
-----
    from src.db.operations import upsert_jobs, get_jobs, get_job_stats

    inserted = upsert_jobs(normalised_jobs)
    print(f"{inserted} new jobs added")
"""

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.exc import IntegrityError

from src.core.logger import get_logger
from src.db.database import get_session
from src.db.models import Job

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Write operations
# ---------------------------------------------------------------------------

def upsert_jobs(jobs: list[dict[str, Any]]) -> int:
    """
    Insert new jobs, silently skipping duplicates.

    Duplicate detection is based on the UNIQUE constraint
    (source, external_id) defined in the ORM model.

    Parameters
    ----------
    jobs:
        List of normalised job dicts as produced by the normalizer.

    Returns
    -------
    int
        Number of records actually inserted (not counting skipped duplicates).
    """
    if not jobs:
        logger.info("upsert_jobs: no jobs to insert")
        return 0

    inserted = 0
    skipped = 0

    for raw in jobs:
        job = Job(
            external_id=str(raw.get("external_id", "")),
            source=str(raw.get("source", "")),
            title=str(raw.get("title", "")),
            company=str(raw.get("company", "")),
            location=str(raw.get("location", "")),
            description=str(raw.get("description", "")),
            url=str(raw.get("url", "")),
            tags=json.dumps(raw.get("tags", []), ensure_ascii=False),
            posted_at=str(raw.get("posted_at", "")),
            scraped_at=datetime.now(timezone.utc),
        )

        try:
            with get_session() as session:
                session.add(job)
            inserted += 1
        except IntegrityError:
            # Duplicate (source, external_id) — expected, not an error.
            skipped += 1
        except Exception as exc:
            logger.error(
                "Failed to insert job external_id=%r source=%r: %s",
                raw.get("external_id"),
                raw.get("source"),
                exc,
            )

    logger.info(
        "upsert_jobs complete: %d inserted, %d skipped (duplicates)",
        inserted,
        skipped,
    )
    return inserted


# ---------------------------------------------------------------------------
# Read operations
# ---------------------------------------------------------------------------

def get_jobs(
    source: str | None = None,
    keyword: str | None = None,
    page: int = 1,
    per_page: int = 20,
) -> list[Job]:
    """
    Retrieve paginated job records with optional filters.

    Parameters
    ----------
    source   : Filter by source name (e.g. 'remoteok').
    keyword  : Case-insensitive substring match against title and company.
    page     : 1-indexed page number.
    per_page : Records per page.

    Returns
    -------
    list[Job]
    """
    with get_session() as session:
        query = session.query(Job)

        if source:
            query = query.filter(Job.source == source)

        if keyword:
            kw = f"%{keyword.lower()}%"
            from sqlalchemy import or_
            query = query.filter(
                or_(
                    Job.title.ilike(kw),
                    Job.company.ilike(kw),
                )
            )

        offset = (page - 1) * per_page
        jobs = (
            query.order_by(Job.scraped_at.desc())
            .offset(offset)
            .limit(per_page)
            .all()
        )

        # Detach from session before returning so callers don't need an
        # active session to access the objects.
        session.expunge_all()
        return jobs


def get_job_by_id(job_id: int) -> Job | None:
    """Return a single Job by its primary key, or None if not found."""
    with get_session() as session:
        job = session.get(Job, job_id)
        if job:
            session.expunge(job)
        return job


def get_job_stats() -> dict[str, Any]:
    """
    Return aggregated statistics about stored jobs.

    Returns
    -------
    dict with keys:
        total       : int  — total job count across all sources.
        by_source   : dict — count per source name.
        last_scraped: str  — ISO timestamp of the most recently scraped job,
                             or empty string if no jobs exist.
    """
    with get_session() as session:
        total: int = session.query(Job).count()

        from sqlalchemy import func
        rows = (
            session.query(Job.source, func.count(Job.id))
            .group_by(Job.source)
            .all()
        )
        by_source = {src: cnt for src, cnt in rows}

        latest = (
            session.query(Job.scraped_at)
            .order_by(Job.scraped_at.desc())
            .first()
        )
        last_scraped = (
            latest[0].isoformat() if latest and latest[0] else ""
        )

    return {
        "total": total,
        "by_source": by_source,
        "last_scraped": last_scraped,
    }
