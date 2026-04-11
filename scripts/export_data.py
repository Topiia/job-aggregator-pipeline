"""
Data export script for the Job Aggregator.

Dumps the entire MongoDB database into flat file (CSV) and JSON representations
for localized downstream review.
"""

import csv
import json
from pathlib import Path
import os
import sys

# Ensure the root of the project is securely inside sys path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.core.config import config
from src.db.mongo import get_collection

def export_data():
    coll = get_collection()
    
    # Sort by posted_at descending
    cursor = coll.find({}).sort("posted_at", -1)
    
    columns = ["id", "external_id", "source", "title", "company", "location", "url", "description", "tags", "posted_at", "scraped_at"]
    
    rows = []
    data_json = []
    
    for doc in cursor:
        row = [
            doc.get("_id", ""),
            doc.get("external_id", ""),
            doc.get("source", ""),
            doc.get("title", ""),
            doc.get("company", ""),
            doc.get("location", ""),
            doc.get("url", ""),
            doc.get("description", ""),
            ",".join(doc.get("tags", [])), # simple string join for CSV
            doc.get("posted_at", ""),
            doc.get("scraped_at", "").isoformat() if hasattr(doc.get("scraped_at", ""), "isoformat") else str(doc.get("scraped_at", ""))
        ]
        rows.append(row)
        
        # for JSON output, map `_id` to `id` for consistency
        json_doc = dict(doc)
        json_doc["id"] = json_doc.pop("_id", None)
        if hasattr(json_doc.get("scraped_at"), "isoformat"):
            json_doc["scraped_at"] = json_doc["scraped_at"].isoformat()
        data_json.append(json_doc)

    csv_path = Path(config.DATA_PATH) / "jobs.csv"
    json_path = Path(config.DATA_PATH) / "jobs.json"

    # Write CSV rigidly conforming to columns layout natively
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data_json, f, indent=2)

    print(f"Exported {len(rows)} records to CSV and JSON.")


if __name__ == "__main__":
    export_data()
