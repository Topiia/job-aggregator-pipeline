"""
SQLAlchemy ORM model for the jobs table.

A single unified schema represents job listings from all sources.
Deduplication is enforced via a UNIQUE constraint on (source, external_id).
"""

import json
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


class Job(Base):
    """
    Unified job listing record.

    Fields
    ------
    id          : Auto-incremented surrogate primary key.
    external_id : Source-native identifier (e.g. RemoteOK slug, HN item id).
    source      : Data origin — 'remoteok' | 'arbeitnow' | 'hackernews' | 'weworkremotely'.
    title       : Job title.
    company     : Hiring company name.
    location    : Location string (may be 'Remote', 'Anywhere', city, etc.).
    description : Full or truncated job description (plain text, HTML stripped).
    url         : Canonical application / job-detail URL.
    tags        : JSON-encoded list of tags / tech stack keywords.
    posted_at   : ISO-8601 datetime string indicating when the job was posted.
    scraped_at  : UTC timestamp of when this record was written to the DB.
    """

    __tablename__ = "jobs"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    external_id: str = Column(String(255), nullable=False)
    source: str = Column(String(64), nullable=False)
    title: str = Column(String(512), nullable=False)
    company: str = Column(String(256), nullable=False, default="")
    location: str = Column(String(256), nullable=False, default="")
    description: str = Column(Text, nullable=False, default="")
    url: str = Column(String(2048), nullable=False, default="")
    tags: str = Column(Text, nullable=False, default="[]")
    posted_at: str = Column(String(64), nullable=False, default="")
    scraped_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Deduplication: same job from the same source is never inserted twice.
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_source_external_id"),
    )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def tags_as_list(self) -> list[str]:
        """Deserialize the JSON-encoded tags column into a Python list."""
        try:
            return json.loads(self.tags)
        except (json.JSONDecodeError, TypeError):
            return []

    def __repr__(self) -> str:
        return (
            f"<Job id={self.id} source={self.source!r} "
            f"title={self.title!r} company={self.company!r}>"
        )
