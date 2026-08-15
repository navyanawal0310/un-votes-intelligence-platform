from packages.warehouse.database import get_connection
from packages.analytics.subject_trends import find_subjects


con = get_connection()

print("=" * 80)
print("NUCLEAR SUBJECT SEARCH")
print("=" * 80)

result = find_subjects(
    con,
    "nuclear",
)

print(result.to_string(index=False))

print()
print(f"Subjects found: {len(result):,}")

con.close()