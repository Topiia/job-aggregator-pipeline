import sys
import os

# Ensure project root is on the path when invoked as a script (not a module)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.scheduler import run_daily_pipeline

if __name__ == "__main__":
    run_daily_pipeline()
