"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import Any
from app.models import Source
from pydantic import BaseModel, Field


class SourceResponse(BaseModel):
    """Response schema for a data source."""

    id: int
    name: str
    type: str
    description: str | None = None
    enabled: bool
    meta: dict[str, Any] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_source(cls, source: Source):
        # Ensure we return the stored meta field as `meta`
        return cls(
            id=source.id,
            name=source.name,
            type=source.type,
            description=source.description,
            enabled=source.enabled,
            meta=source.meta,
            created_at=source.created_at,
        )


class DataPointSchema(BaseModel):
    """Schema for a single data point."""

    timestamp: datetime
    data: dict[str, Any] = Field(..., description="Arbitrary data fields")


class DataResponse(BaseModel):
    """Response schema for data endpoint."""

    source: str
    type: str
    data: list[dict[str, Any]]
    aggregates: dict[str, dict[str, float]] = Field(
        default_factory=dict, description="Statistics for numeric fields"
    )
    # Metadata about fields (units, display formatting, which aggregates apply)
    field_metadata: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Per-field metadata: unit, format string, aggregates to include",
    )
    period: dict[str, datetime | None] = Field(
        default_factory=dict, description="Time range of the data"
    )
    total_count: int
    returned_count: int


class ErrorResponse(BaseModel):
    """Error response schema."""

    detail: str
