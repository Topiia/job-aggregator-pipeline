"""
Pydantic schemas for the incoming and outgoing data bounds on the API layer.
"""

from typing import Dict, List

from pydantic import BaseModel, ConfigDict


class JobResponse(BaseModel):
    id: str
    title: str
    company: str
    location: str
    url: str
    source: str
    posted_at: str

    model_config = ConfigDict(from_attributes=True)


class JobsListResponse(BaseModel):
    count: int
    results: List[JobResponse]


class StatsResponse(BaseModel):
    total_stored_jobs: int
    sources: Dict[str, int]
    last_scraped: str
