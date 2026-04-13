"""
One-time duplicate detection script.
Checks MongoDB for records sharing (source, external_id).
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db.mongo import get_collection

coll = get_collection()

pipeline = [
    {
        "$group": {
            "_id": {
                "source": "$source",
                "external_id": "$external_id"
            },
            "count": {"$sum": 1},
            "ids": {"$push": "$_id"}
        }
    },
    {
        "$match": {
            "count": {"$gt": 1}
        }
    }
]

duplicates = list(coll.aggregate(pipeline))
total_docs = coll.count_documents({})

print(f"Total docs: {total_docs}")
print(f"Duplicate groups: {len(duplicates)}")

if duplicates:
    print("Sample duplicates:")
    for d in duplicates[:5]:
        print(d)
else:
    print("SAFE: No duplicates found.")
