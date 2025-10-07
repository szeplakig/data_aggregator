"""Application configuration."""

from typing import Any
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.app.adapters.openmeteo import OpenMeteoConfig


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="allow"
    )

    # Database
    database_url: str = "postgresql://postgres:postgres@db:5432/data_aggregator"

    # API
    api_prefix: str = "/api"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost",
    ]

    # Scheduler
    default_fetch_interval_minutes: int = 180  # 3 hours to avoid rate limiting
    # Whether to perform an immediate fetch on application startup
    startup_fetch: bool = True


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Data source configurations - easily extensible
DATA_SOURCES_CONFIG: list[dict[str, Any]] = [
    {
        "name": "openmeteo",
        "type": "hourly",
        "description": "Open-Meteo Weather API - Hourly forecast data",
        "adapter_class": "OpenMeteoAdapter",
        "fetch_interval_minutes": 60,
        "enabled": True,
        "config": OpenMeteoConfig(
            base_url="https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": 48.2081,
                "longitude": 16.3713,
                "hourly": "temperature_2m,precipitation,wind_speed_10m",
                "timezone": "UTC",
            },
            field_mapping={
                "temperature_2m": "temperature",
                "wind_speed_10m": "wind_speed",
            },
            numeric_fields=["temperature", "precipitation", "wind_speed"],
            location="Vienna, Austria",
            location_coords="48.2081°N, 16.3713°E",
            unique_key="timestamp",
            # Use timestamp as unique key so hourly points aren't deduplicated
            # on a non-existent field like `created_at`.
            fields={
                "temperature": {
                    "unit": "°C",
                    "format": "{:.1f}",
                    "aggregates": ["avg", "min", "max", "count"],
                    "display_name": "Temperature",
                },
                "precipitation": {
                    "unit": "mm",
                    "format": "{:.2f}",
                    "aggregates": ["sum", "avg", "count"],
                    "display_name": "Precipitation",
                },
                "wind_speed": {
                    "unit": "km/h",
                    "format": "{:.2f}",
                    "aggregates": ["avg", "min", "max", "count"],
                    "display_name": "Wind Speed",
                },
            },
        ),
    },
]
