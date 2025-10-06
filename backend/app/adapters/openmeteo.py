"""OpenMeteo weather API adapter."""

from datetime import datetime
from typing import Any
import httpx

from app.adapters import DataSourceAdapter


class OpenMeteoAdapter(DataSourceAdapter):
    """Adapter for Open-Meteo weather API."""

    async def fetch_data(self) -> list[dict[str, Any]]:
        """Fetch weather data from Open-Meteo API."""
        base_url = self.config["base_url"]
        params = self.config["params"]
        field_mapping = self.config.get("field_mapping", {})

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()

        # Transform API response to common format
        hourly_data = data.get("hourly", {})
        timestamps = hourly_data.get("time", [])

        data_points = []
        for i, time_str in enumerate(timestamps):
            # Parse timestamp
            timestamp = datetime.fromisoformat(time_str.replace("Z", "+00:00"))

            # Build data point
            point = {"timestamp": timestamp}

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
        return self.config.get("numeric_fields", [])
