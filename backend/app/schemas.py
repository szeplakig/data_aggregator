"""Pydantic schemas for API requests and responses."""

from datetime import datetime
from typing import Any
from backend.app.models import Source
from pydantic import BaseModel, Field


class SourceResponse(BaseModel):
    """Response schema for a data source."""

    id: int
    name: str
    type: str
    description: str | None = None
    enabled: bool
    metadata: dict[str, Any] | None = None  # Include location and other metadata
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_source(cls, source: Source):
        return cls(
            id=source.id,
            name=source.name,
            type=source.type,
            description=source.description,
            enabled=source.enabled,
            metadata=source.metadata,
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
    period: dict[str, datetime | None] = Field(
        default_factory=dict, description="Time range of the data"
    )
    total_count: int
    returned_count: int


class ErrorResponse(BaseModel):
    """Error response schema."""

    detail: str
