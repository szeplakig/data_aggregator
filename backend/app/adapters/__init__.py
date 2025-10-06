"""Generic data source adapter interface."""

from abc import ABC, abstractmethod
from typing import Any


class DataSourceAdapter(ABC):
    """
    Abstract base class for data source adapters.

    Each adapter implements this interface to fetch data from
    different APIs. The adapter transforms API-specific data
    into a common format that the system can work with.
    """

    def __init__(self, config: dict[str, Any]):
        """
        Initialize adapter with configuration.

        Args:
            config: Adapter-specific configuration dict
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
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """Get the name of this data source."""
        pass

    @abstractmethod
    def get_data_type(self) -> str:
        """Get the data type ('hourly' or 'daily')."""
        pass

    @abstractmethod
    def get_numeric_fields(self) -> list[str]:
        """
        Get list of numeric field names for aggregation.

        Returns:
            List of field names that contain numeric data
        """
        pass

    def get_description(self) -> str:
        """Get description of the data source."""
        return self.config.get("description", "")
