"""
Test script for the Aggregator Orchestration layer.

Runs the controlled job aggregation pipeline and prints the summary.
"""

import sys
import os
import json

# Ensure the project root is on sys.path when run as a script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.aggregator import run_aggregation


def main():
    print("=" * 60)
    print("  Aggregator Orchestration Test")
    print("=" * 60)
    print("Running pipeline...")
    
    summary = run_aggregation()
    
    print("\n" + "=" * 60)
    print("  Aggregation Summary")
    print("=" * 60)
    print(json.dumps(summary, indent=2))
    
    if summary.get("stop_reason"):
        print("\n[!] Pipeline stopped early:")
        print(f"    {summary['stop_reason']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
