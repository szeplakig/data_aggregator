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
