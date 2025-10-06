"""Main FastAPI application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.scheduler import initialize_scheduler, get_scheduler
from app.api import router

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting up...")

    # Initialize database
    init_db()
    logger.info("Database initialized")

    # Initialize and start scheduler
    scheduler = initialize_scheduler()
    scheduler.start()
    logger.info("Scheduler started")

    # Optionally fetch data immediately on startup
    logger.info("Fetching initial data...")
    await scheduler.fetch_all_now()
    logger.info("Initial data fetched")

    yield

    # Shutdown
    logger.info("Shutting down...")
    scheduler.shutdown()
    logger.info("Scheduler stopped")


# Create FastAPI application
app = FastAPI(
    title="Data Aggregator API",
    description=(
        "Generic data aggregator that fetches data from multiple sources "
        "and provides a unified API with automatic aggregations."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(router, prefix=settings.api_prefix)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Data Aggregator API",
        "docs": "/docs",
        "api": settings.api_prefix,
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    scheduler = get_scheduler()
    return {
        "status": "healthy",
        "scheduler_running": scheduler.scheduler.running,
        "registered_sources": list(scheduler.adapters.keys()),
    }
