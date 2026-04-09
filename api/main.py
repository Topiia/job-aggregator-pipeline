"""
FastAPI application entry point for the Job Aggregator.

This is a STRICTLY READ-ONLY application boundary. 
It does not, under any circumstances, trigger scraping, alter state, 
background tasks, or contact external services.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router

app = FastAPI(
    title="Job Aggregator API",
    description="Read-only interface for aggregated daily job feeds.",
    version="1.0.0",
)

# Standard permissive read-only CORS implementation.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(router)
