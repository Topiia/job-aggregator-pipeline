# Job Aggregator

A fully controlled data pipeline and job aggregation dashboard.

## Features

- **Robust Infinite Scroll:** A high-performance cursor-based pagination system with stable React state machine logic. Includes double-guard fetch conditions preventing duplicate API calls and perfect edge-case handling for end-of-data states.
- **Advanced Filtering:** Filter by keyword, source, and time windows (e.g., last 10 days by default, up to 90 days for specific searches).
- **Time-based Data Windowing:** Intelligent SQL-level boundary filters to maintain data relevance while optimizing backend payload delivery.
- **Responsive Dashboard:** Beautiful, fluid UI built with React and Tailwind CSS.
- **FastAPI Backend:** Lightweight, asynchronous Python backend serving the curated job datasets.

## Architecture

- **Frontend:** React + TypeScript + Vite/Next (Running on `npm run dev`)
- **Backend:** Python + FastAPI (Running with Uvicorn `api.main:app`)
- **Database:** Internal operations pipeline mapping strictly controlled queried boundaries.

## Recent Updates

- Refactored `Dashboard.tsx` to handle true state-machine based infinite scrolling.
- Purged all memory leak risks associated with React IntersectionObserver overlapping.
- Integrated accurate `hasMore` pagination boundaries avoiding rate limits and 429 errors.
