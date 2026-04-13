"""
FastAPI application entry point for the Job Aggregator.

This is a STRICTLY READ-ONLY application boundary. 
It does not, under any circumstances, trigger scraping, alter state, 
background tasks, or contact external services.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from api.middleware import RateLimitMiddleware, BotProtectionMiddleware
from src.db.mongo import get_collection, _ensure_indexes

app = FastAPI(
    title="Job Aggregator API",
    description="Read-only interface for aggregated daily job feeds.",
    version="1.0.0",
)

@app.on_event("startup")
def startup_event():
    _ensure_indexes(get_collection())

# Restrict CORS to the custom production frontend domain and Vercel deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://jobs.topiiaa.site",
        "https://job-aggregator-pipeline.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Enforce globally scoped memory-backed IP rate limits aggressively restricting spam
app.add_middleware(RateLimitMiddleware)

# Block bots and automated tools missing or forging User-Agent headers
app.add_middleware(BotProtectionMiddleware)
