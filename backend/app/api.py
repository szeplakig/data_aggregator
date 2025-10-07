"""API endpoints."""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.repository import DataRepository
from app.schemas import SourceResponse, DataResponse, ErrorResponse
from app.aggregator import DataAggregator
from app.scheduler import get_scheduler

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
    db: Session = Depends(get_db),
) -> DataResponse:
    """
    Get data from a specific source.

    The response includes:
    - Raw data points
    - Aggregated statistics for numeric fields
    - Time period information
    """
    repo = DataRepository(db)

    # Get source
    source = repo.get_source_by_name(source_name)
    if not source:
        raise HTTPException(status_code=404, detail=f"Source '{source_name}' not found")

    # Calculate time filter if hours specified
    from_time = None
    to_time = None
    if hours:
        to_time = datetime.utcnow()
        from_time = to_time - timedelta(hours=hours)

    # Get data points
    data_points = repo.get_data_points(
        source_id=source.id,
        limit=limit,
        offset=offset,
        from_time=from_time,
        to_time=to_time,
    )

    # Get total count
    total_count = repo.count_data_points(
        source_id=source.id, from_time=from_time, to_time=to_time
    )

    # Transform to response format
    data_list = []
    for point in data_points:
        data_dict = {"timestamp": point.timestamp, **point.data}
        data_list.append(data_dict)

    # Calculate aggregates according to per-source field metadata
    aggregates = {}
    field_metadata: dict[str, dict] = {}
    if data_list:
        # Load field metadata persisted in the Source.meta
        source_meta = source.meta or {}
        fields_opts = (
            source_meta.get("fields", {}) if isinstance(source_meta, dict) else {}
        )

        # If adapter is present, ensure numeric fields are covered even if not listed
        scheduler = get_scheduler()
        if source_name in scheduler.adapters:
            adapter_numeric = scheduler.adapters[source_name].get_numeric_fields()
            # Ensure each numeric field has at least an entry in fields_opts
            for f in adapter_numeric:
                fields_opts.setdefault(f, {})
        else:
            # Auto-detect numeric fields and ensure an entry exists
            detected = DataAggregator.detect_numeric_fields(data_list)
            for f in detected:
                fields_opts.setdefault(f, {})

        # Compute aggregates per field using provided options
        aggregates = DataAggregator.aggregate_with_options(data_list, fields_opts)

        # Expose field metadata (units/format/aggregates) to client for formatting
        field_metadata = {}
        for fname, opts in fields_opts.items():
            # only include minimal, safe keys
            field_metadata[fname] = {
                "unit": opts.get("unit"),
                "format": opts.get("format"),
                "aggregates": opts.get("aggregates"),
                "display_name": opts.get("display_name"),
            }

    # Determine time period
    period = {}
    if data_list:
        timestamps = [d["timestamp"] for d in data_list]
        period = {"from": min(timestamps), "to": max(timestamps)}

    return DataResponse(
        source=source_name,
        type=source.type,
        data=data_list,
        aggregates=aggregates,
        field_metadata=field_metadata,
        period=period,
        total_count=total_count,
        returned_count=len(data_list),
    )


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
        "timestamp": datetime.utcnow(),
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
        "timestamp": datetime.utcnow(),
    }
