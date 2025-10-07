"""Database models."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    String,
    Boolean,
    TIMESTAMP,
    ForeignKey,
    Index,
    Text,
    UniqueConstraint,
)
from sqlalchemy import JSON as SA_JSON
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column

if TYPE_CHECKING:
    pass


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class Source(Base):
    """Data source model - stores metadata about data sources."""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'hourly' or 'daily'
    description: Mapped[str | None] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    meta: Mapped[dict | None] = mapped_column("meta", SA_JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(tz=UTC)
    )

    # Relationships
    data_points: Mapped[list["DataPoint"]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )


class DataPoint(Base):
    """Data point model - stores arbitrary JSON data."""

    __tablename__ = "data_points"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.id", ondelete="CASCADE"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )
    data: Mapped[dict] = mapped_column(SA_JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=lambda: datetime.now(tz=UTC)
    )

    # Relationships
    source: Mapped["Source"] = relationship(back_populates="data_points")

    __table_args__ = (
        Index("idx_source_timestamp", "source_id", "timestamp"),
        UniqueConstraint("source_id", "timestamp", name="uq_source_timestamp"),
    )
