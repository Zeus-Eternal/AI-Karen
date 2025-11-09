"""
Data Analysis Tool for AI-Karen
Statistical analysis and data processing capabilities.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
import statistics
from collections import Counter
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class DataAnalysisTool:
    """
    Production-grade data analysis tool.

    Features:
    - Statistical analysis (mean, median, mode, stdev, etc.)
    - Data aggregation and grouping
    - Data filtering and transformation
    - Time series analysis
    - Data validation and quality checks
    - JSON/CSV/dict data processing
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.max_dataset_size = self.config.get('max_dataset_size', 1_000_000)

    async def calculate_statistics(
        self,
        data: List[Union[int, float]]
    ) -> Dict[str, Any]:
        """
        Calculate statistical measures for numeric data.

        Args:
            data: List of numeric values

        Returns:
            Dictionary with statistical measures
        """
        if not data:
            raise ValueError("Empty dataset")

        if len(data) > self.max_dataset_size:
            raise ValueError(f"Dataset too large: {len(data)} (max: {self.max_dataset_size})")

        # Filter out non-numeric values
        numeric_data = [x for x in data if isinstance(x, (int, float))]

        if not numeric_data:
            raise ValueError("No numeric values in dataset")

        result = {
            'count': len(numeric_data),
            'sum': sum(numeric_data),
            'mean': statistics.mean(numeric_data),
            'median': statistics.median(numeric_data),
            'min': min(numeric_data),
            'max': max(numeric_data),
            'range': max(numeric_data) - min(numeric_data)
        }

        # Add mode if possible
        try:
            result['mode'] = statistics.mode(numeric_data)
        except statistics.StatisticsError:
            result['mode'] = None

        # Add standard deviation and variance
        if len(numeric_data) >= 2:
            result['stdev'] = statistics.stdev(numeric_data)
            result['variance'] = statistics.variance(numeric_data)
        else:
            result['stdev'] = None
            result['variance'] = None

        # Add quartiles
        result['q1'] = statistics.quantiles(numeric_data, n=4)[0]
        result['q2'] = statistics.quantiles(numeric_data, n=4)[1]
        result['q3'] = statistics.quantiles(numeric_data, n=4)[2]

        return result

    async def count_values(
        self,
        data: List[Any],
        top_n: Optional[int] = None
    ) -> Dict[Any, int]:
        """
        Count occurrences of each value.

        Args:
            data: List of values
            top_n: Return only top N most common

        Returns:
            Dictionary of value counts
        """
        counter = Counter(data)

        if top_n:
            return dict(counter.most_common(top_n))
        return dict(counter)

    async def filter_data(
        self,
        data: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Filter data based on conditions.

        Args:
            data: List of dictionaries
            filters: Dictionary of field: value filters

        Returns:
            Filtered data
        """
        result = []

        for item in data:
            match = True
            for key, value in filters.items():
                if key not in item or item[key] != value:
                    match = False
                    break
            if match:
                result.append(item)

        return result

    async def group_by(
        self,
        data: List[Dict[str, Any]],
        key: str
    ) -> Dict[Any, List[Dict[str, Any]]]:
        """
        Group data by field value.

        Args:
            data: List of dictionaries
            key: Field to group by

        Returns:
            Dictionary mapping key values to groups
        """
        groups = {}

        for item in data:
            if key not in item:
                continue

            group_key = item[key]
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(item)

        return groups

    async def aggregate(
        self,
        data: List[Dict[str, Any]],
        group_by: str,
        aggregations: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Group and aggregate data.

        Args:
            data: List of dictionaries
            group_by: Field to group by
            aggregations: Dict of field: operation ('sum', 'avg', 'count', 'min', 'max')

        Returns:
            Aggregated results
        """
        groups = await self.group_by(data, group_by)
        results = []

        for group_key, items in groups.items():
            result = {group_by: group_key}

            for field, operation in aggregations.items():
                values = [item.get(field) for item in items if field in item]
                numeric_values = [v for v in values if isinstance(v, (int, float))]

                if operation == 'sum':
                    result[f'{field}_sum'] = sum(numeric_values) if numeric_values else 0
                elif operation == 'avg':
                    result[f'{field}_avg'] = (
                        statistics.mean(numeric_values) if numeric_values else None
                    )
                elif operation == 'count':
                    result[f'{field}_count'] = len(values)
                elif operation == 'min':
                    result[f'{field}_min'] = min(numeric_values) if numeric_values else None
                elif operation == 'max':
                    result[f'{field}_max'] = max(numeric_values) if numeric_values else None

            results.append(result)

        return results

    async def sort_data(
        self,
        data: List[Dict[str, Any]],
        key: str,
        reverse: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Sort data by field.

        Args:
            data: List of dictionaries
            key: Field to sort by
            reverse: Sort in descending order

        Returns:
            Sorted data
        """
        return sorted(data, key=lambda x: x.get(key, 0), reverse=reverse)

    async def pivot_table(
        self,
        data: List[Dict[str, Any]],
        rows: str,
        columns: str,
        values: str,
        aggfunc: str = 'sum'
    ) -> Dict[str, Any]:
        """
        Create a pivot table.

        Args:
            data: List of dictionaries
            rows: Field for rows
            columns: Field for columns
            values: Field for values
            aggfunc: Aggregation function ('sum', 'avg', 'count', 'min', 'max')

        Returns:
            Pivot table as nested dictionary
        """
        pivot = {}

        for item in data:
            if rows not in item or columns not in item or values not in item:
                continue

            row_key = item[rows]
            col_key = item[columns]
            value = item[values]

            if row_key not in pivot:
                pivot[row_key] = {}

            if col_key not in pivot[row_key]:
                pivot[row_key][col_key] = []

            pivot[row_key][col_key].append(value)

        # Apply aggregation
        result = {}
        for row_key, row_data in pivot.items():
            result[row_key] = {}
            for col_key, values in row_data.items():
                numeric_values = [v for v in values if isinstance(v, (int, float))]

                if aggfunc == 'sum':
                    result[row_key][col_key] = sum(numeric_values)
                elif aggfunc == 'avg':
                    result[row_key][col_key] = (
                        statistics.mean(numeric_values) if numeric_values else None
                    )
                elif aggfunc == 'count':
                    result[row_key][col_key] = len(values)
                elif aggfunc == 'min':
                    result[row_key][col_key] = min(numeric_values) if numeric_values else None
                elif aggfunc == 'max':
                    result[row_key][col_key] = max(numeric_values) if numeric_values else None

        return result

    async def detect_outliers(
        self,
        data: List[Union[int, float]],
        method: str = 'iqr',
        threshold: float = 1.5
    ) -> Dict[str, Any]:
        """
        Detect outliers in numeric data.

        Args:
            data: List of numeric values
            method: Detection method ('iqr', 'zscore')
            threshold: Threshold for outlier detection

        Returns:
            Dictionary with outlier info
        """
        numeric_data = [x for x in data if isinstance(x, (int, float))]

        if len(numeric_data) < 4:
            return {'outliers': [], 'outlier_indices': [], 'method': method}

        outliers = []
        outlier_indices = []

        if method == 'iqr':
            # Interquartile range method
            q1 = statistics.quantiles(numeric_data, n=4)[0]
            q3 = statistics.quantiles(numeric_data, n=4)[2]
            iqr = q3 - q1
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr

            for i, value in enumerate(numeric_data):
                if value < lower_bound or value > upper_bound:
                    outliers.append(value)
                    outlier_indices.append(i)

        elif method == 'zscore':
            # Z-score method
            mean = statistics.mean(numeric_data)
            stdev = statistics.stdev(numeric_data)

            for i, value in enumerate(numeric_data):
                z_score = abs((value - mean) / stdev) if stdev > 0 else 0
                if z_score > threshold:
                    outliers.append(value)
                    outlier_indices.append(i)

        return {
            'outliers': outliers,
            'outlier_indices': outlier_indices,
            'outlier_count': len(outliers),
            'method': method,
            'threshold': threshold
        }

    async def normalize_data(
        self,
        data: List[Union[int, float]],
        method: str = 'minmax',
        range_min: float = 0.0,
        range_max: float = 1.0
    ) -> List[float]:
        """
        Normalize numeric data.

        Args:
            data: List of numeric values
            method: Normalization method ('minmax', 'zscore')
            range_min: Minimum value for minmax (default: 0.0)
            range_max: Maximum value for minmax (default: 1.0)

        Returns:
            Normalized data
        """
        numeric_data = [x for x in data if isinstance(x, (int, float))]

        if not numeric_data:
            return []

        if method == 'minmax':
            min_val = min(numeric_data)
            max_val = max(numeric_data)
            range_val = max_val - min_val

            if range_val == 0:
                return [range_min] * len(numeric_data)

            return [
                range_min + (x - min_val) * (range_max - range_min) / range_val
                for x in numeric_data
            ]

        elif method == 'zscore':
            mean = statistics.mean(numeric_data)
            stdev = statistics.stdev(numeric_data) if len(numeric_data) >= 2 else 1

            if stdev == 0:
                return [0.0] * len(numeric_data)

            return [(x - mean) / stdev for x in numeric_data]

        else:
            raise ValueError(f"Unknown normalization method: {method}")

    async def calculate_correlation(
        self,
        x: List[Union[int, float]],
        y: List[Union[int, float]]
    ) -> float:
        """
        Calculate Pearson correlation coefficient.

        Args:
            x: First dataset
            y: Second dataset

        Returns:
            Correlation coefficient (-1 to 1)
        """
        if len(x) != len(y):
            raise ValueError("Datasets must have same length")

        if len(x) < 2:
            raise ValueError("Need at least 2 data points")

        # Filter numeric values
        pairs = [(xi, yi) for xi, yi in zip(x, y)
                 if isinstance(xi, (int, float)) and isinstance(yi, (int, float))]

        if len(pairs) < 2:
            raise ValueError("Need at least 2 numeric pairs")

        x_vals = [p[0] for p in pairs]
        y_vals = [p[1] for p in pairs]

        return statistics.correlation(x_vals, y_vals)

    async def validate_data_quality(
        self,
        data: List[Dict[str, Any]],
        required_fields: List[str],
        field_types: Optional[Dict[str, type]] = None
    ) -> Dict[str, Any]:
        """
        Validate data quality.

        Args:
            data: List of dictionaries
            required_fields: List of required fields
            field_types: Expected types for fields

        Returns:
            Data quality report
        """
        field_types = field_types or {}

        total_records = len(data)
        valid_records = 0
        missing_fields = {field: 0 for field in required_fields}
        type_errors = {field: 0 for field in field_types}
        null_values = {}

        for item in data:
            record_valid = True

            # Check required fields
            for field in required_fields:
                if field not in item or item[field] is None:
                    missing_fields[field] += 1
                    record_valid = False

            # Check field types
            for field, expected_type in field_types.items():
                if field in item and item[field] is not None:
                    if not isinstance(item[field], expected_type):
                        type_errors[field] += 1
                        record_valid = False

            # Count null values
            for key, value in item.items():
                if value is None:
                    null_values[key] = null_values.get(key, 0) + 1

            if record_valid:
                valid_records += 1

        return {
            'total_records': total_records,
            'valid_records': valid_records,
            'invalid_records': total_records - valid_records,
            'validity_rate': valid_records / total_records if total_records > 0 else 0,
            'missing_fields': missing_fields,
            'type_errors': type_errors,
            'null_values': null_values
        }


# Singleton instance
_data_analysis_tool_instance = None


def get_data_analysis_tool(
    config: Optional[Dict[str, Any]] = None
) -> DataAnalysisTool:
    """Get or create singleton data analysis tool instance."""
    global _data_analysis_tool_instance
    if _data_analysis_tool_instance is None:
        _data_analysis_tool_instance = DataAnalysisTool(config)
    return _data_analysis_tool_instance
