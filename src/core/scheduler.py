"""
Scheduler orchestration for the Job Aggregator.

Enforces the strict ONE-RUN-PER-DAY rule.
Maintains execution state via tracking 'data/last_run.json'.
"""

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.core.config import config
from src.core.logger import get_logger
from src.services.aggregator import run_aggregation
from scripts.export_data import export_data

logger = get_logger(__name__)

_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_last_run() -> datetime | None:
    """
    Read the last successful run timestamp from the tracking file.
    
    Returns
    -------
    datetime | None
        The datetime of the last run, or None if the file doesn't exist
        or cannot be parsed.
    """
    last_run_path = Path(config.LAST_RUN_PATH)
    if not last_run_path.exists():
        return None

    try:
        with open(last_run_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            last_run_str = data.get("last_run")
            if last_run_str:
                last_run = datetime.strptime(last_run_str, _DATE_FORMAT)
                if last_run.tzinfo is None:
                    last_run = last_run.replace(tzinfo=timezone.utc)
                return last_run
    except Exception as exc:
        logger.error("Failed to parse last_run file: %s", exc)

    return None


def update_last_run() -> None:
    """
    Records the current timestamp as the last successful run.
    Creates the tracking JSON file and data directory if they don't exist.
    """
    last_run_path = Path(config.LAST_RUN_PATH)
    last_run_path.parent.mkdir(parents=True, exist_ok=True)

    now_str = datetime.now(timezone.utc).strftime(_DATE_FORMAT)
    try:
        with open(last_run_path, "w", encoding="utf-8") as f:
            json.dump({"last_run": now_str}, f, indent=2)
        logger.info("Updated last execution run state to: %s", now_str)
    except Exception as exc:
        logger.error("Failed to update last execution run state: %s", exc)


def can_run_today() -> bool:
    """
    Evaluate if the system is permitted to run based on a strict dual-condition guard.

    Rules (BOTH must be false to allow execution):
    ─────────────────────────────────────────────
    1. Calendar Day Guard  → Block if last_run occurred on today's UTC date.
    2. Minimum Gap Guard   → Block if last_run occurred within the last 20 hours.

    This prevents edge cases where two runs happen at 11:59 PM and 12:01 AM 
    on consecutive calendar days (different days, but only 2 minutes apart).
    """
    last_run = get_last_run()
    if not last_run:
        logger.info("No previous run detected. Execution allowed.")
        return True

    now = datetime.now(timezone.utc)
    same_day = last_run.date() == now.date()
    within_20h = (now - last_run) < timedelta(hours=20)

    if same_day or within_20h:
        hours_elapsed = (now - last_run).total_seconds() / 3600
        logger.warning(
            "Execution blocked: same_day=%s, within_20h=%s (%.1fh elapsed since %s)",
            same_day, within_20h, hours_elapsed, last_run.strftime(_DATE_FORMAT),
        )
        return False

    return True


def run_daily_pipeline() -> None:
    """
    Main entry point for scheduled execution.
    
    Enforces the daily limit. If allowed, invokes the aggregator.
    Only updates the last run timestamp if the aggregator finishes cleanly
    with no critical global stop reasons.
    """
    logger.info("=== Checking Execution Permissions ===")
    
    if not can_run_today():
        logger.info("Pipeline already executed today. Skipping run.")
        return

    logger.info("Execution allowed for today. Proceeding to Aggregator.")
    
    # Run the core aggregation logic
    summary = run_aggregation()
    
    if summary.get("stop_reason") is None:
        logger.info("Aggregator finished cleanly. Executing DB export logic.")
        export_data()
        logger.info("System exported databases to flat files securely.")
        
        logger.info("Recording successful run.")
        update_last_run()
    else:
        logger.warning(
            "Aggregator stopped prematurely (%s). Last run tracker NOT updated.",
            summary["stop_reason"]
        )

