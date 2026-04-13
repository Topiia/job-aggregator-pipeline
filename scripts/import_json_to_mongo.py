"""
One-Time Data Restoration Script
Reads from data/jobs.json and safely imports into MongoDB.
Running this multiple times will safely skip duplicates.
"""

import json
import os
import sys
from pathlib import Path
from pymongo import UpdateOne
from pymongo.errors import BulkWriteError

# Ensure project root is in sys path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.logger import get_logger
from src.db.mongo import get_collection

logger = get_logger("import_json_to_mongo")

def main():
    json_path = Path("data/jobs.json")
    
    if not json_path.exists():
        print(f"Error: Could not find '{json_path}'. No data to import.")
        return

    print(f"Loading data from {json_path}...")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in '{json_path}': {e}")
        return

    total_records = len(data)
    print(f"Total records loaded: {total_records}")
    
    if total_records == 0:
        print("No records to import.")
        return

    print("Connecting to MongoDB...")
    try:
        # Uses the main app's connection logic natively, including MONGO_URI loading
        coll = get_collection()
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return

    operations = []
    skipped_invalid = 0
    
    for row in data:
        source = row.get("source")
        ext_id = row.get("external_id")
        
        if not source or not ext_id:
            logger.warning(f"Skipping record missing source or external_id: {row}")
            skipped_invalid += 1
            continue

        # 1. Validation & ID Generation Handling
        _id = row.get("id") or row.get("_id")
        if not _id:
            _id = f"{source}::{ext_id}"
            
        doc = dict(row)
        # Clean up mapping to enforce raw Mongo Schema 
        doc.pop("id", None)
        doc.pop("_id", None)
        doc["_id"] = _id
        
        # 2. Safe Idempotent Insert Logic (Bulk Upsert)
        operations.append(
            UpdateOne(
                {"_id": _id},
                {"$set": doc},
                upsert=True
            )
        )

    if not operations:
        print(f"Skipped {skipped_invalid} invalid records. Nothing to insert.")
        return

    print("Beginning idempotent MongoDB import operation...")
    
    try:
        result = coll.bulk_write(operations, ordered=False)
        inserted_new = result.upserted_count
        skipped_duplicates = total_records - inserted_new - skipped_invalid
        errors = 0
        
        print("\n--- IMPORT SUMMARY ---")
        print(f"Total records loaded: {total_records}")
        print(f"Inserted count: {inserted_new}")
        print(f"Skipped duplicates: {skipped_duplicates}")
        if skipped_invalid > 0:
             print(f"Skipped invalid: {skipped_invalid}")
        print(f"Errors (if any): {errors}")
        
    except BulkWriteError as bwe:
        errors = len(bwe.details.get("writeErrors", []))
        print(f"\n--- IMPORT SUMMARY (ERRORS DETECTED) ---")
        print(f"Total records loaded: {total_records}")
        print(f"Errors (if any): {errors}")
        print(f"Details: {bwe.details.get('writeErrors')[:3]}") # Truncated strict error snippet 
    except Exception as e:
        print(f"Fatal error during MongoDB write: {e}")

if __name__ == "__main__":
    main()
