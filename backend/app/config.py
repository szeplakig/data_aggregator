"""Application configuration."""

from typing import Any
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


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
        "fetch_interval_minutes": 180,  # 3 hours to avoid rate limiting
        "enabled": True,
        "config": {
            "base_url": "https://api.open-meteo.com/v1/forecast",
            "params": {
                "latitude": 48.2081,
                "longitude": 16.3713,
                "hourly": "temperature_2m,precipitation,wind_speed_10m",
                "timezone": "UTC",
            },
            "field_mapping": {
                "temperature_2m": "temperature",
                "wind_speed_10m": "wind_speed",
            },
            "numeric_fields": ["temperature", "precipitation", "wind_speed"],
            "location": "Vienna, Austria",  # Display location
            "location_coords": "48.2081°N, 16.3713°E",
        },
    },
    {
        "name": "coincap",
        "type": "hourly",
        "description": "CoinCap API - Cryptocurrency prices",
        "adapter_class": "CoinCapAdapter",
        "fetch_interval_minutes": 180,  # 3 hours to avoid rate limiting
        "enabled": True,
        "config": {
            "base_url": "https://api.coincap.io/v2/assets",
            "params": {"limit": 5},
            "field_mapping": {
                "priceUsd": "price_usd",
                "changePercent24Hr": "change_24h",
                "marketCapUsd": "market_cap_usd",
            },
            "numeric_fields": ["price_usd", "change_24h", "market_cap_usd"],
        },
    },
]
