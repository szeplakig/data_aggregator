"""OpenMeteo weather API adapter."""

from datetime import datetime
from typing import Any, Dict

import httpx

from app.adapters import BaseConfigModel, DataSourceAdapter


class OpenMeteoConfig(BaseConfigModel):
    """Typed configuration for OpenMeteoAdapter."""

    base_url: str
    params: dict
    field_mapping: dict[str, str] = {}
    numeric_fields: list[str] = []
    description: str | None = None
    location: str | None = None
    location_coords: str | None = None
    fields: dict[str, dict[str, Any]] | None = None
    unique_key: str | None = None


class OpenMeteoAdapter(DataSourceAdapter[OpenMeteoConfig]):
    """Adapter for Open-Meteo weather API."""

    async def fetch_data(self) -> list[dict[str, Any]]:
        """Fetch weather data from Open-Meteo API."""
        base_url = self.config.base_url
        params = self.config.params
        field_mapping = self.config.field_mapping or {}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()

        # Transform API response to common format
        hourly_data: Dict[str, list] = data.get("hourly", {})
        timestamps = hourly_data.get("time", [])

        data_points: list[dict[str, Any]] = []
        for i, time_str in enumerate(timestamps):
            # Parse timestamp
            timestamp = datetime.fromisoformat(time_str.replace("Z", "+00:00"))

            # Build data point
            point: dict[str, Any] = {"timestamp": timestamp}

            # Extract all hourly fields
            for api_field, values in hourly_data.items():
                if api_field == "time":
                    continue

                # Apply field mapping if configured
                field_name = field_mapping.get(api_field, api_field)
                point[field_name] = values[i] if i < len(values) else None

            data_points.append(point)

        return data_points

    def get_source_name(self) -> str:
        """Get source name."""
        return "openmeteo"

    def get_data_type(self) -> str:
        """Get data type."""
        return "hourly"

    def get_numeric_fields(self) -> list[str]:
        """Get numeric fields for aggregation."""
        return list(self.config.numeric_fields or [])

    def get_metadata(self) -> dict[str, Any] | None:
        """Return metadata for OpenMeteo source.

        Leverage configuration fields such as `location`, `location_coords`
        and the `fields` map (if present) to build metadata used by the
        repository. This mirrors the previous inlined behavior in the
        scheduler while keeping metadata logic inside the adapter.
        """
        metadata: dict[str, Any] = {}
        if self.config.location is not None:
            metadata["location"] = self.config.location
        loc_coords = getattr(self.config, "location_coords", None)
        if loc_coords is not None:
            metadata["location_coords"] = loc_coords
        # The config may include a `fields` map describing per-field metadata
        fields_map = getattr(self.config, "fields", None)
        if fields_map is not None and isinstance(fields_map, dict):
            metadata["fields"] = fields_map

        return metadata if metadata else None

    def get_unique_key(self) -> str | None:
        """Return configured unique_key if present."""
        return self.config.unique_key
