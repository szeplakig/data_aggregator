"""Adapter factory for creating data source adapters."""

from typing import Type
from app.adapters import DataSourceAdapter
from app.adapters.openmeteo import OpenMeteoAdapter
from app.adapters.coincap import CoinCapAdapter


# Registry of available adapters
ADAPTER_REGISTRY: dict[str, Type[DataSourceAdapter]] = {
    "OpenMeteoAdapter": OpenMeteoAdapter,
    "CoinCapAdapter": CoinCapAdapter,
}


def create_adapter(adapter_class_name: str, config: dict) -> DataSourceAdapter:
    """
    Factory function to create adapter instances.

    Args:
        adapter_class_name: Name of the adapter class
        config: Configuration dict for the adapter

    Returns:
        Instantiated adapter

    Raises:
        ValueError: If adapter class is not found
    """
    adapter_class = ADAPTER_REGISTRY.get(adapter_class_name)

    if not adapter_class:
        raise ValueError(
            f"Unknown adapter class: {adapter_class_name}. "
            f"Available: {list(ADAPTER_REGISTRY.keys())}"
        )

    return adapter_class(config)


def register_adapter(name: str, adapter_class: Type[DataSourceAdapter]) -> None:
    """
    Register a new adapter class.

    Args:
        name: Name to register the adapter under
        adapter_class: The adapter class
    """
    ADAPTER_REGISTRY[name] = adapter_class
