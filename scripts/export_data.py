"""
Data export script for the Job Aggregator.

Dumps the entire SQLite database matching exact columns mapped internally 
into flat file (CSV) and JSON representations for localized downstream review.
"""

import sqlite3
import csv
import json
from pathlib import Path
import os
import sys

# Ensure the root of the project is securely inside sys path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.core.config import config

def export_data():
    conn = sqlite3.connect(config.DB_PATH)
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT id, title, company, location, url, source, posted_at
        FROM jobs
        ORDER BY posted_at DESC
    """).fetchall()

    columns = ["id", "title", "company", "location", "url", "source", "posted_at"]

    csv_path = Path(config.DATA_PATH) / "jobs.csv"
    json_path = Path(config.DATA_PATH) / "jobs.json"

    # Write CSV rigidly conforming to columns layout natively
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)

    # Bind mapped structural lists -> dict payloads formatting JSON smoothly 
    data = [dict(zip(columns, row)) for row in rows]
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    conn.close()

    print(f"Exported {len(rows)} records to CSV and JSON.")


if __name__ == "__main__":
    export_data()
