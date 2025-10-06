"""Generic repository for data-agnostic CRUD operations."""

from datetime import datetime
from typing import Any, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

from app.models import Source, DataPoint


class DataRepository:
    """Generic repository - no knowledge of specific data structures."""

    def __init__(self, db: Session):
        self.db = db

    # Source operations
    def get_source_by_name(self, name: str) -> Optional[Source]:
        """Get source by name."""
        stmt = select(Source).where(Source.name == name)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_all_sources(self, enabled_only: bool = False) -> list[Source]:
        """Get all sources."""
        stmt = select(Source)
        if enabled_only:
            stmt = stmt.where(Source.enabled == True)  # noqa: E712
        return list(self.db.execute(stmt).scalars().all())

    def create_source(
        self,
        name: str,
        type: str,
        description: Optional[str] = None,
        enabled: bool = True,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Source:
        """Create a new source."""
        source = Source(
            name=name,
            type=type,
            description=description,
            enabled=enabled,
            metadata=metadata or {},
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return source

    def get_or_create_source(
        self,
        name: str,
        type: str,
        description: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Source:
        """Get existing source or create new one."""
        source = self.get_source_by_name(name)
        if source:
            # Update metadata if provided
            if metadata and source.metadata != metadata:
                source.metadata = metadata
                self.db.commit()
                self.db.refresh(source)
            return source
        return self.create_source(name, type, description, metadata=metadata)

    # Data point operations
    def save_data_points(
        self, source_id: int, data_points: list[dict[str, Any]]
    ) -> int:
        """
        Save multiple data points.

        Args:
            source_id: ID of the source
            data_points: List of dicts with 'timestamp' and other fields

        Returns:
            Number of data points saved
        """
        db_points = []
        for point in data_points:
            timestamp = point.pop("timestamp")
            db_point = DataPoint(source_id=source_id, timestamp=timestamp, data=point)
            db_points.append(db_point)

        self.db.bulk_save_objects(db_points)
        self.db.commit()
        return len(db_points)

    def get_data_points(
        self,
        source_id: int,
        limit: Optional[int] = None,
        offset: int = 0,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None,
    ) -> list[DataPoint]:
        """
        Get data points with optional filtering.

        Args:
            source_id: ID of the source
            limit: Maximum number of results
            offset: Number of results to skip
            from_time: Filter data points after this time
            to_time: Filter data points before this time

        Returns:
            List of data points
        """
        stmt = select(DataPoint).where(DataPoint.source_id == source_id)

        # Apply time filters
        if from_time:
            stmt = stmt.where(DataPoint.timestamp >= from_time)
        if to_time:
            stmt = stmt.where(DataPoint.timestamp <= to_time)

        # Order by timestamp descending (newest first)
        stmt = stmt.order_by(DataPoint.timestamp.desc())

        # Apply pagination
        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        return list(self.db.execute(stmt).scalars().all())

    def count_data_points(
        self,
        source_id: int,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None,
    ) -> int:
        """Count data points with optional time filtering."""
        stmt = select(func.count(DataPoint.id)).where(DataPoint.source_id == source_id)

        if from_time:
            stmt = stmt.where(DataPoint.timestamp >= from_time)
        if to_time:
            stmt = stmt.where(DataPoint.timestamp <= to_time)

        return self.db.execute(stmt).scalar_one()

    def delete_old_data_points(self, source_id: int, before_time: datetime) -> int:
        """Delete data points older than specified time."""
        stmt = select(DataPoint).where(
            and_(DataPoint.source_id == source_id, DataPoint.timestamp < before_time)
        )
        points = self.db.execute(stmt).scalars().all()
        count = len(points)

        for point in points:
            self.db.delete(point)

        self.db.commit()
        return count
