"""
API route definitions for the Job Aggregator.

Strictly read-only mapped endpoint handlers.
"""

from fastapi import APIRouter, HTTPException, Query

from api.schemas import JobResponse, JobsListResponse, StatsResponse
from src.core.logger import get_logger
from src.db.mongo import get_jobs as m_get_jobs, get_job_by_id as m_get_job_by_id, get_stats as m_get_stats

logger = get_logger(__name__)

router = APIRouter()


@router.get("/jobs", response_model=JobsListResponse)
def get_jobs(
    source: str | None = Query(None, description="Filter by generic source name"),
    keyword: str | None = Query(None, description="Match title or company name"),
    limit: int = Query(20, description="Max job objects returned"),
    offset: int = Query(0, description="Offset index for pagination"),
    days: int | None = Query(None, description="Time window in days")
):
    """
    Retrieve jobs across the aggregated database limits bounded correctly.
    """
    logger.info("Hit /jobs -> source=%s, keyword=%s, limit=%s, offset=%s, days=%s", source, keyword, limit, offset, days)

    # 1) Soft-cap limits gracefully allowing them without discarding request natively
    if limit > 50:
        logger.warning("Limit exceeded. Capped to 50.")
        limit = 50
    if limit < 1:
        limit = 1

    jobs = m_get_jobs(source=source, keyword=keyword, limit=limit, offset=offset, days=days)
    
    logger.info("Returning %d jobs", len(jobs))
    return {
        "count": len(jobs),
        "results": jobs
    }


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job_by_id(job_id: str):
    """
    Retrieve a singular specific Job execution via ID strictly bounded.
    """
    logger.info("Hit /jobs/%s", job_id)
    
    job = m_get_job_by_id(str(job_id))
    if not job:
        logger.warning("/jobs/%s -> NOT FOUND", job_id)
        raise HTTPException(status_code=404, detail="Job not found")
        
    logger.info("Returning Job %s successfully", job_id)
    return job


@router.get("/stats", response_model=StatsResponse)
def get_stats():
    """
    Retrieve general structural system statistics securely bounded natively.
    """
    logger.info("Hit /stats")
    
    stats_data = m_get_stats()
    
    # Map internal dictionary format to StatsResponse explicitly defined representation.
    payload = {
        "total_stored_jobs": stats_data.get("total", 0),
        "sources": stats_data.get("by_source", {}),
        "last_scraped": stats_data.get("last_scraped", ""),
    }
    
    logger.info("Returning standard metrics format successfully")
    return payload
