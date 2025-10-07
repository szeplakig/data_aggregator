"""Generic data aggregator for calculating statistics."""

import statistics
from typing import Any


class DataAggregator:
    """
    Generic aggregator that calculates statistics for numeric fields.

    Works on any dataset without knowing the field names in advance.
    """

    @staticmethod
    def aggregate(
        data: list[dict[str, Any]], numeric_fields: list[str]
    ) -> dict[str, dict[str, float]]:
        """
        Calculate aggregates for specified numeric fields.

        Args:
            data: List of data point dictionaries
            numeric_fields: List of field names to aggregate

        Returns:
            Dict mapping field names to their statistics:
            {
                "field_name": {
                    "avg": 123.45,
                    "min": 100.0,
                    "max": 150.0,
                    "sum": 2469.0,
                    "count": 20
                }
            }
        """
        if not data:
            return {}

        aggregates = {}

        for field in numeric_fields:
            # Extract values for this field (skip None values)
            values = []
            for point in data:
                value = point.get(field)
                if value is not None:
                    try:
                        # Convert to float to handle both int and float
                        values.append(float(value))
                    except (ValueError, TypeError):
                        # Skip non-numeric values
                        continue

            # Calculate statistics if we have values
            if values:
                aggregates[field] = {
                    "avg": round(statistics.mean(values), 6),
                    "min": round(min(values), 6),
                    "max": round(max(values), 6),
                    "sum": round(sum(values), 6),
                    "count": len(values),
                }

        return aggregates

    @staticmethod
    def detect_numeric_fields(data: list[dict[str, Any]]) -> list[str]:
        """
        Automatically detect numeric fields in the data.

        Args:
            data: List of data point dictionaries

        Returns:
            List of field names that contain numeric data
        """
        if not data:
            return []

        # Sample first few records to detect types
        sample_size = min(10, len(data))
        sample = data[:sample_size]

        numeric_fields = set()

        for point in sample:
            for key, value in point.items():
                # Skip timestamp and non-numeric fields
                if key == "timestamp":
                    continue

                # Check if value is numeric
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    numeric_fields.add(key)
                elif isinstance(value, str):
                    # Try to convert string to float
                    try:
                        float(value)
                        numeric_fields.add(key)
                    except (ValueError, TypeError):
                        pass

        return sorted(list(numeric_fields))

    @staticmethod
    def aggregate_with_options(
        data: list[dict[str, Any]],
        field_options: dict[str, dict[str, Any]],
        default_aggregates: list[str] | None = None,
    ) -> dict[str, dict[str, float]]:
        """
        Calculate aggregates for fields according to per-field options.

        Args:
            data: List of data point dictionaries
            field_options: Mapping from field name to options. Supported options:
                - aggregates: list[str] e.g. ["avg","min","max","sum","count"]
            default_aggregates: Aggregates to use when field has no explicit list.

        Returns:
            Dict mapping field names to their computed statistics.
        """
        if not data:
            return {}

        if default_aggregates is None:
            # sensible default: exclude `sum` to avoid nonsensical sums like temperature
            default_aggregates = ["avg", "min", "max", "count"]

        aggregates = {}

        for field, opts in field_options.items():
            wanted = opts.get("aggregates", default_aggregates)

            # Extract numeric values for this field
            values = []
            for point in data:
                val = point.get(field)
                if val is None:
                    continue
                try:
                    values.append(float(val))
                except (ValueError, TypeError):
                    continue

            if not values:
                continue

            stats: dict[str, float] = {}
            if "avg" in wanted:
                stats["avg"] = round(sum(values) / len(values), 6)
            if "min" in wanted:
                stats["min"] = round(min(values), 6)
            if "max" in wanted:
                stats["max"] = round(max(values), 6)
            if "sum" in wanted:
                stats["sum"] = round(sum(values), 6)
            if "count" in wanted:
                stats["count"] = len(values)

            if stats:
                aggregates[field] = stats

        return aggregates
