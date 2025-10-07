"""Generic repository for data-agnostic CRUD operations."""

from datetime import datetime, timezone
import json
from typing import Any, Optional
import logging
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session

from app.models import Source, DataPoint

logger = logging.getLogger(__name__)


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
            meta=metadata or {},
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
            if metadata and source.meta != metadata:
                source.meta = metadata
                self.db.commit()
                self.db.refresh(source)
            return source
        return self.create_source(name, type, description, metadata=metadata)

    # Data point operations
    def save_data_points(
        self,
        source_id: int,
        data_points: list[dict[str, Any]],
        unique_key: str | None = None,
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

        # unique_key handling below will be used to deduplicate when provided

        # Helper to extract nested values
        def _get_nested(value: dict[str, Any], path: str) -> Any:
            parts = path.split(".")
            v: Any = value
            for p in parts:
                if not isinstance(v, dict):
                    return None
                if p in v:
                    v = v[p]
                else:
                    return None
            return v

        def _extract_unique_val_from_point(
            point: dict[str, Any], key: str, ts: datetime | None
        ) -> Any:
            if key == "timestamp":
                return ts
            if key in point:
                return point.get(key)
            for container in ("data", "payload"):
                if isinstance(point.get(container), dict) and key in point[container]:
                    return point[container].get(key)
            if "." in key:
                return _get_nested(point, key)
            return None

        def _extract_unique_val_from_db(e: DataPoint, key: str) -> Any:
            if key == "timestamp":
                return e.timestamp
            if key in e.data:
                return e.data.get(key)
            for container in ("data", "payload"):
                if isinstance(e.data.get(container), dict) and key in e.data[container]:
                    return e.data[container].get(key)
            if "." in key:
                parts = key.split(".")
                v: Any = e.data
                for p in parts:
                    if not isinstance(v, dict) or p not in v:
                        return None
                    v = v[p]
                return v
            return None

        def _normalize_val(v: Any) -> Any:
            # datetimes -> canonical UTC iso string
            if isinstance(v, datetime):
                if v.tzinfo is None:
                    v = v.replace(tzinfo=timezone.utc)
                else:
                    v = v.astimezone(timezone.utc)
                return v.replace(microsecond=0).isoformat()

            # dict/list/tuple -> stable JSON string (hashable)
            if isinstance(v, (dict, list, tuple)):
                try:
                    return json.dumps(v, sort_keys=True, default=str)
                except Exception:
                    return str(v)

            # primitive/hashable types -> return as-is if hashable, else str
            try:
                hash(v)
                return v
            except Exception:
                return str(v)

        # Prepare existing sets for unique_key branch
        existing_keys_norm: set[tuple[str, Any]] = set()
        existing_unique_vals: set[Any] = set()
        if unique_key and unique_key != "timestamp":
            stmt = select(DataPoint).where(DataPoint.source_id == source_id)
            existing = list(self.db.execute(stmt).scalars().all())
            for e in existing:
                key_val = _extract_unique_val_from_db(e, unique_key)
                existing_unique_vals.add(_normalize_val(key_val))
                existing_keys_norm.add(
                    (_normalize_val(e.timestamp), _normalize_val(key_val))
                )

        # Track seen values within this batch
        seen_unique_vals: set[Any] = set()
        seen_timestamps: set[str] = set()

        # Iterate incoming points, extract/normalize timestamps and unique values,
        # and filter duplicates before creating DataPoint objects
        for point in data_points:
            ts = point.pop("timestamp", None)
            if not ts and unique_key:
                candidate = _extract_unique_val_from_point(point, unique_key, None)
                if isinstance(candidate, datetime):
                    ts = candidate
                elif isinstance(candidate, str):
                    try:
                        ts = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
                    except Exception:
                        ts = None

            if isinstance(ts, datetime):
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                else:
                    ts = ts.astimezone(timezone.utc)
                # Round/truncate to second precision to avoid duplicates from
                # sub-second differences.
                ts = ts.replace(microsecond=0)
            if not ts:
                continue

            if unique_key and unique_key != "timestamp":
                unique_val = _extract_unique_val_from_point(point, unique_key, ts)
                norm_unique = _normalize_val(unique_val)
                if (
                    norm_unique in existing_unique_vals
                    or norm_unique in seen_unique_vals
                ):
                    continue
                norm_ts = _normalize_val(ts)
                if (norm_ts, norm_unique) in existing_keys_norm:
                    continue
                seen_unique_vals.add(norm_unique)
            else:
                norm_ts = _normalize_val(ts)
                if norm_ts in seen_timestamps:
                    continue
                seen_timestamps.add(norm_ts)

            db_point = DataPoint(source_id=source_id, timestamp=ts, data=point)
            db_points.append(db_point)

        if not db_points:
            return 0

        # Try bulk insert. If the DB raises IntegrityError because some rows
        # already exist (unique constraint on source_id+timestamp), fall back
        # to inserting one-by-one and skip duplicates.
        from sqlalchemy.exc import IntegrityError

        try:
            self.db.bulk_save_objects(db_points)
            self.db.commit()
            return len(db_points)
        except IntegrityError:
            # rollback and try per-row inserts to skip duplicates
            self.db.rollback()
            saved = 0
            for obj in db_points:
                try:
                    self.db.add(obj)
                    self.db.commit()
                    saved += 1
                except IntegrityError:
                    # duplicate - skip
                    self.db.rollback()
                    continue
            return saved

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
