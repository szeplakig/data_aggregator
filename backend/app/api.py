"""API endpoints."""

import logging
from datetime import UTC, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.repository import DataRepository
from app.schemas import SourceResponse, DataResponse, ErrorResponse
from app.scheduler import get_scheduler
from backend.app.endpoint_handlers.get_data_handler import GetDataHandler

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/sources",
    response_model=list[SourceResponse],
    summary="List all data sources",
    description="Get a list of all configured data sources with their metadata",
)
def get_sources(
    enabled_only: bool = Query(False, description="Only return enabled sources"),
    db: Session = Depends(get_db),
) -> list[SourceResponse]:
    """Get all data sources."""
    repo = DataRepository(db)
    sources = repo.get_all_sources(enabled_only=enabled_only)
    return [SourceResponse.from_source(s) for s in sources]


@router.get(
    "/data/{source_name}",
    response_model=DataResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get data from a source",
    description=(
        "Retrieve data points from a specific source with optional filtering. "
        "Automatically calculates aggregates (avg, min, max, sum, count) for numeric fields."
    ),
)
def get_data(
    source_name: str,
    limit: int = Query(
        100, ge=1, le=10000, description="Maximum number of data points to return"
    ),
    offset: int = Query(0, ge=0, description="Number of data points to skip"),
    hours: Optional[int] = Query(
        None, ge=1, description="Only return data from last N hours"
    ),
    handler: GetDataHandler = Depends(GetDataHandler),
) -> DataResponse:
    """
    Get data from a specific source.

    The response includes:
    - Raw data points
    - Aggregated statistics for numeric fields
    - Time period information
    """
    return handler.handle(source_name, limit, offset, hours)


@router.post(
    "/fetch/{source_name}",
    summary="Trigger immediate data fetch",
    description="Manually trigger an immediate fetch for a specific data source",
)
async def trigger_fetch(source_name: str, db: Session = Depends(get_db)) -> dict:
    """Manually trigger a data fetch for a specific source."""
    scheduler = get_scheduler()

    if source_name not in scheduler.adapters:
        raise HTTPException(
            status_code=404,
            detail=f"Source '{source_name}' not found or not registered",
        )

    # Fetch data immediately
    adapter = scheduler.adapters[source_name]
    await scheduler.fetch_and_store(adapter)

    return {
        "message": f"Data fetch triggered for {source_name}",
        "timestamp": datetime.now(tz=UTC),
    }


@router.post(
    "/fetch-all",
    summary="Trigger fetch for all sources",
    description="Manually trigger an immediate fetch for all registered data sources",
)
async def trigger_fetch_all() -> dict:
    """Manually trigger a data fetch for all sources."""
    scheduler = get_scheduler()
    await scheduler.fetch_all_now()

    return {
        "message": "Data fetch triggered for all sources",
        "sources": list(scheduler.adapters.keys()),
        "timestamp": datetime.now(tz=UTC),
    }
