"""CoinCap cryptocurrency API adapter."""

from datetime import datetime, timezone
from typing import Any
import httpx

from app.adapters import DataSourceAdapter


class CoinCapAdapter(DataSourceAdapter):
    """Adapter for CoinCap cryptocurrency API."""

    async def fetch_data(self) -> list[dict[str, Any]]:
        """Fetch crypto data from CoinCap API."""
        base_url = self.config["base_url"]
        params = self.config.get("params", {})
        field_mapping = self.config.get("field_mapping", {})

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()

        # Get current timestamp for all data points
        current_time = datetime.now(timezone.utc)

        # Transform API response to common format
        assets = data.get("data", [])

        data_points = []
        for asset in assets:
            # Build data point with timestamp
            point = {"timestamp": current_time}

            # Add asset name/id
            point["asset_id"] = asset.get("id")
            point["asset_name"] = asset.get("name")
            point["symbol"] = asset.get("symbol")

            # Extract numeric fields with mapping
            for api_field, value in asset.items():
                if api_field in ["id", "name", "symbol", "rank"]:
                    continue

                # Apply field mapping if configured
                field_name = field_mapping.get(api_field, api_field)

                # Convert to float if possible
                try:
                    point[field_name] = float(value) if value is not None else None
                except (ValueError, TypeError):
                    point[field_name] = value

            data_points.append(point)

        return data_points

    def get_source_name(self) -> str:
        """Get source name."""
        return "coincap"

    def get_data_type(self) -> str:
        """Get data type."""
        return "hourly"

    def get_numeric_fields(self) -> list[str]:
        """Get numeric fields for aggregation."""
        return self.config.get("numeric_fields", [])
