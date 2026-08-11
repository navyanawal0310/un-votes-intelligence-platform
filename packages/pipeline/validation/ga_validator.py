"""
Validation rules for the official UN General Assembly voting dataset.
"""

from __future__ import annotations

import pandas as pd


EXPECTED_COLUMNS = {
    "undl_id",
    "ms_code",
    "ms_name",
    "ms_vote",
    "date",
    "session",
    "session_number",
    "resolution",
    "draft",
    "committee_report",
    "meeting",
    "title",
    "agenda_title",
    "subjects",
    "vote_note",
    "total_yes",
    "total_no",
    "total_abstentions",
    "total_non_voting",
    "total_ms",
    "undl_link",
}


VALID_VOTES = {"Y", "N", "A", "X"}


def validate_ga_dataset(df: pd.DataFrame) -> None:
    """
    Validate the official UN General Assembly voting dataset.
    """

    # ---------------------------------------------------------
    # 1. Schema
    # ---------------------------------------------------------

    missing_columns = EXPECTED_COLUMNS - set(df.columns)

    assert not missing_columns, (
        f"Missing GA columns: {sorted(missing_columns)}"
    )

    # ---------------------------------------------------------
    # 2. Required fields
    # ---------------------------------------------------------

    required_columns = [
        "undl_id",
        "ms_code",
        "ms_name",
        "ms_vote",
        "date",
        "session",
        "session_number",
        "resolution",
    ]

    for column in required_columns:
        assert df[column].notna().all(), (
            f"Null values found in required column: {column}"
        )

    # ---------------------------------------------------------
    # 3. Vote codes
    # ---------------------------------------------------------

    invalid_votes = (
        set(df["ms_vote"].dropna().unique())
        - VALID_VOTES
    )

    assert not invalid_votes, (
        f"Invalid GA vote codes: {sorted(invalid_votes)}"
    )

    # ---------------------------------------------------------
    # 4. Resolution / Member State grain
    # ---------------------------------------------------------

    duplicate_votes = df.duplicated(
        subset=["resolution", "ms_code"]
    ).sum()

    assert duplicate_votes == 0, (
        f"Duplicate resolution/member votes: {duplicate_votes}"
    )

    # ---------------------------------------------------------
    # 5. Date validation
    # ---------------------------------------------------------

    dates = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    assert dates.notna().all(), (
        "Invalid GA dates found."
    )

    assert dates.min() >= pd.Timestamp("1946-01-10"), (
        f"GA date before General Assembly first session: "
        f"{dates.min()}"
    )

    assert dates.max() <= pd.Timestamp("2025-12-30"), (
        f"GA date after dataset end: {dates.max()}"
    )

    # ---------------------------------------------------------
    # 6. Session validation
    # ---------------------------------------------------------

    valid_session_format = df["session"].astype(str).str.fullmatch(
        r"\d+|\d+sp|\d+emsp"
    )

    assert valid_session_format.all(), (
        "GA session contains unexpected formats."
    )

    assert df["session_number"].notna().all(), (
        "GA session_number contains null values."
    )

    assert (df["session_number"] >= 1).all(), (
        "Invalid GA session numbers found."
    )

    # ---------------------------------------------------------
    # 7. Session normalization consistency
    # ---------------------------------------------------------

    extracted_session_numbers = (
        df["session"]
        .astype(str)
        .str.extract(r"^(\d+)", expand=False)
        .astype("Int64")
    )

    assert (
        extracted_session_numbers
        .eq(df["session_number"])
        .all()
    ), (
        "GA session_number does not match the official session value."
    )

    # ---------------------------------------------------------
    # 8. Aggregate vote validation
    # ---------------------------------------------------------

    vote_counts = (
        df.groupby("resolution")["ms_vote"]
        .value_counts()
        .unstack(fill_value=0)
    )

    for vote in VALID_VOTES:
        if vote not in vote_counts.columns:
            vote_counts[vote] = 0

    totals = (
        df.groupby("resolution")[
            [
                "total_yes",
                "total_no",
                "total_abstentions",
                "total_non_voting",
                "total_ms",
            ]
        ]
        .first()
    )

    calculated = pd.DataFrame(
        {
            "total_yes": vote_counts["Y"],
            "total_no": vote_counts["N"],
            "total_abstentions": vote_counts["A"],
            "total_non_voting": vote_counts["X"],
        }
    )

    calculated["total_ms"] = calculated.sum(axis=1)

    calculated = calculated.sort_index()
    totals = totals.sort_index()

    assert calculated.index.equals(totals.index), (
        "Resolution mismatch between vote records and totals."
    )

    for column in [
        "total_yes",
        "total_no",
        "total_abstentions",
        "total_non_voting",
        "total_ms",
    ]:
        mismatches = calculated[column] != totals[column]

        assert not mismatches.any(), (
            f"GA aggregate mismatch in {column}: "
            f"{mismatches.sum()} resolutions"
        )

    print("GA dataset validation: PASSED")