"""Generic data source adapter interface.

This module defines a small adapter contract and a lightweight
convention for adapter-specific configuration using pydantic
BaseModel types. Adapters can continue to be instantiated with a
plain dict (for backward compatibility) — the base class will
validate/convert the dict into the adapter's declared ConfigModel.
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class BaseConfigModel(BaseModel):
    unique_key: str | None = None


class DataSourceAdapter[ConfigModelType: BaseConfigModel](ABC):
    """
    Abstract base class for data source adapters.

    Each adapter must declare a `ConfigModel` (a subclass of
    `pydantic.BaseModel`) as a class attribute describing its configuration.
    When an adapter is instantiated with a plain dict, the base class will
    parse it into the declared model. Adapters should then access
    configuration using attribute access instead of dict lookups.
    """

    def __init__(self, config: ConfigModelType):
        """
        Initialize adapter with configuration.

        Args:
            config: Adapter-specific configuration.
        """
        self.config = config

    @abstractmethod
    async def fetch_data(self) -> list[dict[str, Any]]:
        """
        Fetch data from the source.

        Returns:
            List of data points, each must contain:
            - 'timestamp': datetime object
            - other fields: any JSON-serializable data
        """
        ...

    @abstractmethod
    def get_source_name(self) -> str:
        """Get the name of this data source."""
        ...

    @abstractmethod
    def get_data_type(self) -> str:
        """Get the data type ('hourly' or 'daily')."""
        ...

    @abstractmethod
    def get_numeric_fields(self) -> list[str]:
        """
        Get list of numeric field names for aggregation.

        Returns:
            List of field names that contain numeric data
        """
        ...

    def get_description(self) -> str:
        """Get description of the data source (if provided in config)."""
        return getattr(self.config, "description", "")

    @abstractmethod
    def get_metadata(self) -> dict[str, Any] | None:
        """Return metadata about the source.

        Adapters that expose metadata MUST implement this method. This
        enforces that source-specific logic lives inside adapters instead of
        being extracted by generic code (scheduler/repository).
        """
        ...

    @abstractmethod
    def get_unique_key(self) -> str | None:
        """Return the optional unique_key used to deduplicate incoming points.

        Default implementation looks for a `unique_key` entry in the
        adapter config (supports pydantic models and plain dicts).
        """
        ...
