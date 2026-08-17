import pandas as pd

from packages.analytics.change_points import (
    detect_change_points,
    confirmed_change_points,
    change_point_summary,
)


def section(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


# ---------------------------------------------------------
# Synthetic known-change dataset
# ---------------------------------------------------------

rows = []

for year in range(2000, 2011):

    if year <= 2004:
        position = 40.0

    else:
        position = 80.0

    rows.append(
        {
            "ms_code": "TST",
            "subject": "TEST ISSUE",
            "year": year,
            "position_score": position,
        }
    )


df = pd.DataFrame(rows)


section("SYNTHETIC CHANGE-POINT TEST")

print(df.to_string(index=False))


changes = detect_change_points(
    df,
    before_window=3,
    after_window=3,
    magnitude_threshold=10.0,
    effect_threshold=0.8,
    persistence_window=3,
)

print("\nDetected changes:")

print(
    changes.to_string(
        index=False
    )
)


assert not changes.empty

confirmed = confirmed_change_points(
    changes
)

assert not confirmed.empty


# The known structural change occurs at 2005.
detected_year = int(
    confirmed.iloc[0]["change_year"]
)

print(
    f"\nDetected change year: "
    f"{detected_year}"
)

assert detected_year == 2005


summary = change_point_summary(
    changes
)

print("\nSUMMARY")

for key, value in summary.items():
    print(
        f"{key}: {value}"
    )


assert summary[
    "confirmed_count"
] >= 1


section(
    "CHANGE-POINT TEST COMPLETE"
)

print(
    "Change-point test runner: PASSED"
)