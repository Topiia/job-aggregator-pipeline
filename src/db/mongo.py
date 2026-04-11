"""
MongoDB layer for the Job Aggregator.

Replaces SQLite completely in production path. Provides connection handling,
indexing, idempotency, and query capabilities.

Usage
-----
    from src.db.mongo import upsert_jobs, get_jobs, get_stats

    inserted = upsert_jobs(normalised_jobs)
"""

import hashlib
from datetime import datetime, timezone, timedelta
from typing import Any

from pymongo import MongoClient, UpdateOne
from pymongo.collection import Collection

from src.core.config import config
from src.core.logger import get_logger

logger = get_logger(__name__)

# Single global client instance
_client: MongoClient | None = None
_collection: Collection | None = None

def get_collection() -> Collection:
    """
    Lazy initialization of MongoDB client and collection.
    Ensures indexes are created on first access.
    """
    global _client, _collection
    if _collection is not None:
        return _collection

    if not config.MONGO_URI:
        # Fallback or error if missing. We can log but we shouldn't necessarily crash immediately
        # unless it's impossible to continue. The aggregator might run local, or railway has it.
        logger.warning("MONGO_URI is not set. Connecting to localhost fallback.")
        uri = "mongodb://localhost:27017"
    else:
        uri = config.MONGO_URI

    logger.info("Connecting to MongoDB...")
    _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    db = _client[config.MONGO_DB_NAME]
    _collection = db["jobs"]
    
    # 2. Enforce MongoDB Index
    _ensure_indexes(_collection)
    
    return _collection


def _ensure_indexes(coll: Collection) -> None:
    """Create necessary unique and performance indexes."""
    logger.info("Ensuring MongoDB indexes...")
    # 2. Enforce MongoDB Index: Unique constraint on (source, external_id)
    coll.create_index(
        [("source", 1), ("external_id", 1)],
        unique=True
    )
    # Additional indexes for query performance
    coll.create_index([("posted_at", -1)])
    coll.create_index([("scraped_at", -1)])
    

# ---------------------------------------------------------------------------
# Write operations
# ---------------------------------------------------------------------------

def upsert_jobs(jobs: list[dict[str, Any]]) -> int:
    """
    Insert new jobs securely using MongoDB bulk upsert.
    Enforces stable unique identifiers and date formatting.
    """
    if not jobs:
        logger.info("upsert_jobs: no jobs to insert")
        return 0

    coll = get_collection()
    operations = []
    
    for raw in jobs:
        # 1. Stable Unique Identifier handling
        ext_id = str(raw.get("external_id") or "").strip()
        title = str(raw.get("title") or "").strip()
        company = str(raw.get("company") or "").strip()
        url = str(raw.get("url") or "").strip()
        
        if not ext_id or ext_id.lower() == "unknown":
            # Generate stable ID if missing (Critical Verification Checklist #1)
            raw_url = str(raw.get("url") or "")
            ext_id = hashlib.sha256(raw_url.encode("utf-8")).hexdigest()
            
        source = str(raw.get("source", "unknown"))
        _id = f"{source}::{ext_id}"
        
        # 3. Date Normalization (Critical for Filters)
        # Ensure posted_at is valid ISO-8601 UTC format. 
        posted_at_str = str(raw.get("posted_at") or "").strip()
        is_valid_date = False
        if posted_at_str:
            try:
                # Basic standard-library ISO format check
                datetime.fromisoformat(posted_at_str.replace("Z", "+00:00"))
                is_valid_date = True
            except ValueError:
                pass

        if not is_valid_date:
            # Fallback to current UTC time if totally missing or invalid
            posted_at_str = datetime.now(timezone.utc).isoformat()
        
        scraped_time = datetime.now(timezone.utc)
        doc = {
            "_id": _id,
            "external_id": ext_id,
            "source": source,
            "title": title,
            "company": company,
            "location": str(raw.get("location", "")),
            "description": str(raw.get("description", "")),
            "url": url,
            "tags": raw.get("tags", []), # List format preserved
            "posted_at": posted_at_str,
        }
        
        operations.append(
            UpdateOne(
                {"_id": _id},
                {
                    "$setOnInsert": doc,
                    "$set": {"scraped_at": scraped_time}
                },
                upsert=True
            )
        )

    if not operations:
        return 0
        
    try:
        result = coll.bulk_write(operations, ordered=False)
        inserted_count = result.upserted_count
        skipped = len(jobs) - inserted_count
        logger.info("upsert_jobs complete: %d inserted, %d skipped (duplicates)", inserted_count, skipped)
        return inserted_count
    except Exception as exc:
        logger.error("Failed to execute bulk upsert in MongoDB: %s", exc)
        return 0


# ---------------------------------------------------------------------------
# Read operations
# ---------------------------------------------------------------------------

def _map_to_api_format(doc: dict) -> dict:
    """Helper to map MongoDB document to the format expected by FastAPI responses."""
    if not doc:
        return {}
    # Maps internal `_id` back to standard `id`
    return {
        "id": doc["_id"],
        "external_id": doc.get("external_id", ""),
        "source": doc.get("source", ""),
        "title": doc.get("title", ""),
        "company": doc.get("company", ""),
        "location": doc.get("location", ""),
        "description": doc.get("description", ""),
        "url": doc.get("url", ""),
        "tags": doc.get("tags", []),
        "posted_at": doc.get("posted_at", ""),
        "scraped_at": doc.get("scraped_at", "")
    }

def get_jobs(
    source: str | None = None,
    keyword: str | None = None,
    limit: int = 20,
    offset: int = 0,
    days: int | None = None
) -> list[dict]:
    """
    Retrieve job records mirroring the old SQLite limits and bounds.
    """
    limit = max(1, min(limit, 50))
    coll = get_collection()
    
    query = {}
    
    # Smart Data Windowing: Enforce recency constraints
    if days is not None:
        active_days = max(1, days)
    elif source or keyword:
        active_days = 90
    else:
        active_days = 10
        
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=active_days)
    query["posted_at"] = {"$gte": cutoff_date.isoformat()}
    
    if source:
        query["source"] = source.strip().lower()
        
    if keyword:
        kw = f".*{keyword}.*"
        query["$or"] = [
            {"title": {"$regex": kw, "$options": "i"}},
            {"company": {"$regex": kw, "$options": "i"}}
        ]
        
    # Sort deterministically
    cursor = coll.find(query).sort([("posted_at", -1), ("_id", -1)]).skip(offset).limit(limit)
    
    return [_map_to_api_format(doc) for doc in cursor]


def get_job_by_id(job_id: str) -> dict | None:
    """Return a single Job by its primary key, or None if not found."""
    coll = get_collection()
    doc = coll.find_one({"_id": job_id})
    if doc:
        return _map_to_api_format(doc)
    return None


def get_stats() -> dict[str, Any]:
    """
    Return aggregated statistics about stored jobs.
    Uses MongoDB aggregation pipeline.
    """
    coll = get_collection()
    
    total = coll.count_documents({})
    
    pipeline = [
        {"$group": {"_id": "$source", "count": {"$sum": 1}}}
    ]
    by_source = {doc["_id"]: doc["count"] for doc in coll.aggregate(pipeline)}
    
    latest_cursor = coll.find({}, {"scraped_at": 1}).sort("scraped_at", -1).limit(1)
    latest_docs = list(latest_cursor)
    
    last_scraped = ""
    if latest_docs and "scraped_at" in latest_docs[0]:
        scraped_val = latest_docs[0]["scraped_at"]
        if isinstance(scraped_val, datetime):
            last_scraped = scraped_val.isoformat()
        else:
            last_scraped = str(scraped_val)
            
    return {
        "total": total,
        "by_source": by_source,
        "last_scraped": last_scraped,
    }

# ---------------------------------------------------------------------------
# Execution Lock (Scheduler state)
# ---------------------------------------------------------------------------

def get_mongo_last_run() -> datetime | None:
    """Return the timestamp of the last successful run recorded in MongoDB."""
    coll = get_collection()
    state_coll = coll.database["system_state"]
    doc = state_coll.find_one({"_id": "last_run"})
    if doc and "timestamp" in doc:
        try:
            return datetime.fromisoformat(doc["timestamp"].replace("Z", "+00:00"))
        except ValueError:
            return None
    return None

def update_mongo_last_run() -> None:
    """Record the current time as the latest successful pipeline run."""
    coll = get_collection()
    state_coll = coll.database["system_state"]
    now_str = datetime.now(timezone.utc).isoformat()
    state_coll.update_one(
        {"_id": "last_run"},
        {"$set": {"timestamp": now_str}},
        upsert=True
    )

