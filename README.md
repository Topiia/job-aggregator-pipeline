# Topia Job Aggregator Pipeline

A production-grade, highly controlled job aggregation system and dashboard. Designed strictly for **reliability, IP-ban immunity, and stateless cloud deployments**.

![Dashboard](https://img.shields.io/badge/Frontend-React%20%2B%20Tailwind-blue) ![Backend](https://img.shields.io/badge/Backend-FastAPI-green) ![Database](https://img.shields.io/badge/Database-SQLite-lightgrey) ![Status](https://img.shields.io/badge/Status-Production%20Ready-success)

## 🏗️ System Architecture

This project strictly divorces the **Data Extraction Pipeline** from the **API Serving Layer**.

1. **The Scraper (Pipeline):** Triggered externally (via cron/Windows Task Scheduler). It runs strictly once per day, limits requests, and dumps data into SQLite and JSON/CSV flat files.
2. **The API (Server):** A lightning-fast, 100% read-only FastAPI instance that NEVER triggers scraping. It simply reads the bounded SQLite database and serves it to the frontend.

## 🛡️ Key Production Features

### 1. Ironclad Rate Limiting & Ban Protection
The system runs on a strict request budget (max 15 requests globally per day) with randomized delays (4-6s) between calls. Any HTTP 429 or 403 instantly triggers a global abort to preserve the IP's reputation.

### 2. Stateless Deployment Ready (Railway / Docker)
Engineered to survive ephemeral cloud environments without losing data. All DB files and tracking metadata (`last_run.json`) are seamlessly routed through a `DATA_DIR` environment variable, enabling flawless persistence when mounting to a cloud volume space (e.g., `/app/data`).

### 3. Dual-Guard Scheduler & Self-Healing Timezones
Built to resist double-execution edge cases:
- Evaluates both Calendar Day **AND** Elapsed Time (> 20 hours).
- Mathematical calculations are strictly forced into `timezone.utc` to prevent negative time loops caused by OS clock drift or server migrations.
- If corrupted or future-dated timestamps are detected, the system safely self-heals by rolling timestamps back to `now`.

### 4. Advanced Frontend UX
- **Deterministic Pagination:** Infinite scroll powered by a stable state-machine and predictable SQL sorting directives.
- **Dynamic System Health Indicator:** The UI actively reads the DB extraction timestamp and flashes Green/Yellow/Red, warning end-users if the background pipeline drops behind schedule.
- **Micro-Themed UI:** Features an active CSS variable token system (`--theme-meta`) that universally dictates the application styling AND forces mobile browser UI tabs to match the dashboard's active theme.

## 🚀 Deployment (Cloud / Railway)

1. Connect your GitHub repository.
2. Under volume settings, attach a **Persistent Volume**.
3. Set the mount path to `/app/data`.
4. Inject the environment variable:
   ```bash
   DATA_DIR=/app/data
   ```
5. Trigger the `.scripts/run_scraper.py` file manually or via an external Cron service natively.

## 💻 Local Development

**1. Run the Scraper (Populate Data)**
```bash
venv\Scripts\python.exe scripts\run_scraper.py
```
*(Note: Will block execution if it has been run locally in the last 20 hours).*

**2. Start the Backend API**
```bash
venv\Scripts\python.exe -m uvicorn api.main:app --reload
```

**3. Start the Frontend**
```bash
cd frontend
npm run dev
```
