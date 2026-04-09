"""
Aggregator orchestration service for the Job Aggregator.

Coordinates data collection sources and enforces global safety constraints.
Currently processes a sequence of API sources.
"""

from typing import Any

from src.api_clients import arbeitnow, remoteok
from src.core.logger import get_logger
from src.core.rate_limiter import (
    CriticalHTTPError,
    RateLimiter,
    RateLimitExhausted,
    RuntimeLimitExceeded,
)
from src.db.database import init_db
from src.db.operations import upsert_jobs
from src.services.normalizer import normalize_jobs

logger = get_logger(__name__)


def run_aggregation() -> dict[str, Any]:
    """
    Execute the controlled job aggregation pipeline.
    
    Enforces strict runtime caps and request limits across all stages.
    Returns a summary dictionary of the execution.
    """
    logger.info("=== Starting Aggregation Pipeline ===")
    
    # 1. Initialize DB and RateLimiter
    try:
        init_db()
    except Exception as exc:
        logger.error("Failed to initialize database: %s", exc)
        return _build_summary(stop_reason="DB initialization failed")

    limiter = RateLimiter()
    
    stop_reason: str | None = None
    sources_completed = 0
    sources_failed = 0
    jobs_fetched = 0
    jobs_inserted = 0

    # 2. Define Execution Order (strict list)
    sources = [
        ("remoteok", remoteok),
        ("arbeitnow", arbeitnow),
    ]

    # 3. Source Execution Loop
    for source_name, module in sources:
        logger.info("Evaluating source: %s", source_name)
        
        # Pre-execution Guards
        if limiter.check_timeout():
            stop_reason = f"Timeout reached ({limiter.elapsed_time:.1f}s). Stopping before {source_name}."
            logger.warning(stop_reason)
            break
            
        if not limiter.can_request():
            stop_reason = f"Global request limit reached. Stopping before {source_name}."
            logger.warning(stop_reason)
            break
            
        # Proceed with Fetch
        source_fetched = 0
        source_inserted = 0
        
        try:
            raw_jobs = module.fetch_jobs(limiter)
            
            if raw_jobs:
                source_fetched = len(raw_jobs)
                jobs_fetched += source_fetched
                
                # Normalize and Store
                normalized = normalize_jobs(raw_jobs, source=source_name)
                if normalized:
                    source_inserted = upsert_jobs(normalized)
                    jobs_inserted += source_inserted
                    
            sources_completed += 1
            
            logger.info(
                "Source %s: fetched=%d, inserted=%d", 
                source_name, 
                source_fetched, 
                source_inserted
            )
            
        except CriticalHTTPError as exc:
            stop_reason = f"Critical HTTP Error (429/403) from {source_name}: {exc}"
            logger.critical(stop_reason)
            sources_failed += 1
            break  # Immediate global stop
            
        except RateLimitExhausted as exc:
            stop_reason = f"Rate limit exhausted during {source_name}: {exc}"
            logger.warning(stop_reason)
            sources_failed += 1
            break  # Immediate global stop
            
        except RuntimeLimitExceeded as exc:
            stop_reason = f"Runtime limit exceeded during {source_name}: {exc}"
            logger.warning(stop_reason)
            sources_failed += 1
            break  # Immediate global stop
            
        except Exception as exc:
            # 4. Handle other errors: log and skip source (continue to next)
            logger.error("Unexpected error processing %s: %s", source_name, exc)
            sources_failed += 1
            
    logger.info(
        "=== Aggregation Complete (Time: %.1fs, Requests: %d) ===", 
        limiter.elapsed_time, 
        limiter.request_count
    )

    return _build_summary(
        sources_completed=sources_completed,
        sources_failed=sources_failed,
        jobs_fetched=jobs_fetched,
        jobs_inserted=jobs_inserted,
        total_requests=limiter.request_count,
        stop_reason=stop_reason
    )


def _build_summary(
    sources_completed: int = 0,
    sources_failed: int = 0,
    jobs_fetched: int = 0,
    jobs_inserted: int = 0,
    total_requests: int = 0,
    stop_reason: str | None = None
) -> dict[str, Any]:
    """Helper to consistently build the return summary."""
    return {
        "sources_completed": sources_completed,
        "sources_failed": sources_failed,
        "jobs_fetched": jobs_fetched,
        "jobs_inserted": jobs_inserted,
        "total_requests": total_requests,
        "stop_reason": stop_reason,
    }
