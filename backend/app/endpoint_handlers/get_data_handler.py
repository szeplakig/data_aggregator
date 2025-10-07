from datetime import UTC, datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException

from backend.app.aggregator import DataAggregator
from backend.app.database import get_db
from backend.app.repository import DataRepository
from backend.app.scheduler import get_scheduler
from backend.app.schemas import DataResponse
from sqlalchemy.orm import Session


class GetDataHandler:
    def __init__(
        self,
        db: Session = Depends(get_db),
    ):
        self.db = db

    def handle(self, source_name: str, limit: int, offset: int, hours: Optional[int]):
        repo = DataRepository(self.db)

        source = self._get_source_or_404(repo, source_name)

        from_time, to_time = self._compute_time_window(hours)

        data_points = self._fetch_data_points(
            repo, source, limit, offset, from_time, to_time
        )

        total_count = repo.count_data_points(
            source_id=source.id, from_time=from_time, to_time=to_time
        )

        data_list = self._to_data_list(data_points)

        aggregates, field_metadata = self._compute_aggregates_and_metadata(
            source_name, source, data_list
        )

        period = self._compute_period(data_list)

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

    # --- Extracted helpers ---
    def _get_source_or_404(self, repo: DataRepository, source_name: str):
        source = repo.get_source_by_name(source_name)
        if not source:
            raise HTTPException(
                status_code=404, detail=f"Source '{source_name}' not found"
            )
        return source

    def _compute_time_window(self, hours: Optional[int]):
        if not hours:
            return None, None
        to_time = datetime.now(tz=UTC)
        from_time = to_time - timedelta(hours=hours)
        return from_time, to_time

    def _fetch_data_points(
        self,
        repo: DataRepository,
        source,
        limit: int,
        offset: int,
        from_time,
        to_time,
    ):
        return repo.get_data_points(
            source_id=source.id,
            limit=limit,
            offset=offset,
            from_time=from_time,
            to_time=to_time,
        )

    def _to_data_list(self, data_points):
        return [{"timestamp": p.timestamp, **p.data} for p in data_points]

    def _build_fields_opts(
        self, source_name: str, source_meta: dict, data_list: list[dict]
    ):
        # Load persisted field options (safe default to dict)
        fields_opts = (
            source_meta.get("fields", {}) if isinstance(source_meta, dict) else {}
        )

        # If adapter is present, ensure numeric fields are covered even if not listed
        scheduler = get_scheduler()
        if source_name in scheduler.adapters:
            adapter_numeric = scheduler.adapters[source_name].get_numeric_fields()
            for f in adapter_numeric:
                fields_opts.setdefault(f, {})
        else:
            detected = DataAggregator.detect_numeric_fields(data_list)
            for f in detected:
                fields_opts.setdefault(f, {})

        return fields_opts

    def _compute_aggregates_and_metadata(
        self, source_name: str, source, data_list: list[dict]
    ):
        aggregates = {}
        field_metadata: dict[str, dict] = {}
        if not data_list:
            return aggregates, field_metadata

        source_meta = source.meta or {}
        fields_opts = self._build_fields_opts(source_name, source_meta, data_list)

        aggregates = DataAggregator.aggregate_with_options(data_list, fields_opts)

        for fname, opts in fields_opts.items():
            field_metadata[fname] = {
                "unit": opts.get("unit"),
                "format": opts.get("format"),
                "aggregates": opts.get("aggregates"),
                "display_name": opts.get("display_name"),
            }

        return aggregates, field_metadata

    def _compute_period(self, data_list: list[dict]):
        if not data_list:
            return {}
        timestamps = [d["timestamp"] for d in data_list]
        return {"from": min(timestamps), "to": max(timestamps)}
