from __future__ import annotations

import pandera.pandas as pa
from pandera import Check


ANALYTICAL_VOTES_SCHEMA = pa.DataFrameSchema(
    {
        "undl_id": pa.Column(
            int,
            nullable=False,
        ),

        "ms_code": pa.Column(
            str,
            nullable=False,
        ),

        "body_code": pa.Column(
            str,
            nullable=False,
            checks=Check.isin(["GA", "SC"]),
        ),

        "vote_code": pa.Column(
            str,
            nullable=False,
            checks=Check.isin(["Y", "N", "A", "X"]),
        ),

        "vote_score": pa.Column(
            float,
            nullable=True,
            checks=Check.isin(
                [-1.0, 0.0, 1.0]
            ),
        ),

        "date": pa.Column(
            pa.DateTime,
            nullable=False,
        ),

        "resolution": pa.Column(
            str,
            nullable=False,
        ),

        "year": pa.Column(
            int,
            nullable=False,
            checks=Check.in_range(
                1945,
                2100,
            ),
        ),
    },
    strict=False,
    coerce=True,
)


def validate_analytical_votes(df):
    """
    Validate the Gold analytical voting dataset.

    This is a data contract boundary:
    downstream analytical modules must only consume
    data that passes this validation.
    """

    return ANALYTICAL_VOTES_SCHEMA.validate(
        df,
        lazy=True,
    )