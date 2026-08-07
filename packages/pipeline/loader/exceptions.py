"""
Custom exceptions for warehouse loading.
"""


class WarehouseLoadError(Exception):
    """Raised when loading data into DuckDB fails."""