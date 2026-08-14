"""
Test runner for UN voting warehouse validation.
"""

from packages.warehouse.database import get_connection
from packages.pipeline.validation.warehouse_validator import (
    validate_warehouse,
)


print("Loading UN voting warehouse...")

con = get_connection()

try:
    validate_warehouse(con)
finally:
    con.close()