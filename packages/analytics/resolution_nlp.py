"""
Resolution-level NLP intelligence.

Connects UN voting disagreements to resolution text.

This module is country-agnostic and source-agnostic.
It does not fetch current affairs or geopolitical data.
"""

from __future__ import annotations

from typing import Any

import duckdb
import pandas as pd

from packages.analytics.text_intelligence import (
    classify_text_themes,
    combine_resolution_text,
    text_similarity,
    tfidf_keywords,
)

from packages.analytics.semantic_nlp import (
    discover_topics,
    semantic_similarity,
)

def _query(
    con: duckdb.DuckDBPyConnection,
    sql: str,
    params: list[Any],
) -> pd.DataFrame:
    return con.execute(sql, params).df()


def pair_resolution_nlp(
    con: duckdb.DuckDBPyConnection,
    country_a: str,
    country_b: str,
    top_n: int = 20,
) -> dict[str, Any]:
    """
    Analyse resolution text associated with voting
    disagreements between any two countries.

    No country pair is hard-coded.
    """

    sql = """
        SELECT
            r.resolution_id,
            r.resolution_code,
            r.resolution_title,
            r.agenda_title,
            r.subjects,

            ca.ms_code AS country_a,
            cb.ms_code AS country_b,

            va.vote_code AS vote_code_a,
            vb.vote_code AS vote_code_b,

            va.vote_label AS vote_label_a,
            vb.vote_label AS vote_label_b,

            va.vote_score AS vote_score_a,
            vb.vote_score AS vote_score_b

        FROM fact_votes va

        JOIN dim_country ca
            ON va.country_id = ca.country_id

        JOIN fact_votes vb
            ON va.resolution_id = vb.resolution_id
            AND va.country_id <> vb.country_id

        JOIN dim_country cb
            ON vb.country_id = cb.country_id

        JOIN dim_resolution r
            ON va.resolution_id = r.resolution_id

        WHERE UPPER(ca.ms_code) = UPPER(?)
          AND UPPER(cb.ms_code) = UPPER(?)

          AND va.vote_score IS NOT NULL
          AND vb.vote_score IS NOT NULL

          AND va.vote_score <> vb.vote_score

        ORDER BY r.resolution_id
    """

    disagreements = _query(
        con,
        sql,
        [country_a, country_b],
    )

    if disagreements.empty:
        return {
            "pair": f"{country_a.upper()}-{country_b.upper()}",
            "disagreement_resolutions": 0,
            "keywords": [],
            "similarity_to_agreement": None,
            "resolutions": [],
            "evidence_source": "UN_VOTING",
            "provenance": "UN_VOTES_ANALYZER",
        }

    disagreement_texts = [
        combine_resolution_text(
            row["resolution_title"],
            row["agenda_title"],
            row["subjects"],
        )
        for _, row in disagreements.iterrows()
    ]

    disagreement_texts = [
        x for x in disagreement_texts if x
    ]

    # Agreement corpus: resolutions where both countries
    # cast the same vote.
    agreement_sql = """
        SELECT
            r.resolution_title,
            r.agenda_title,
            r.subjects

        FROM fact_votes va

        JOIN dim_country ca
            ON va.country_id = ca.country_id

        JOIN fact_votes vb
            ON va.resolution_id = vb.resolution_id
            AND va.country_id <> vb.country_id

        JOIN dim_country cb
            ON vb.country_id = cb.country_id

        JOIN dim_resolution r
            ON va.resolution_id = r.resolution_id

        WHERE UPPER(ca.ms_code) = UPPER(?)
          AND UPPER(cb.ms_code) = UPPER(?)

          AND va.vote_score IS NOT NULL
          AND vb.vote_score IS NOT NULL

          AND va.vote_score = vb.vote_score
    """

    agreements = _query(
        con,
        agreement_sql,
        [country_a, country_b],
    )

    agreement_texts = [
        combine_resolution_text(
            row["resolution_title"],
            row["agenda_title"],
            row["subjects"],
        )
        for _, row in agreements.iterrows()
    ]

    agreement_texts = [
        x for x in agreement_texts if x
    ]

    similarity = None

    if disagreement_texts and agreement_texts:
        similarity = text_similarity(
            " ".join(disagreement_texts),
            " ".join(agreement_texts),
        )

    theme_counts: dict[str, int] = {}

    for _, row in disagreements.iterrows():

        text = combine_resolution_text(
            row["resolution_title"],
            row["agenda_title"],
            row["subjects"],
        )

        for theme in classify_text_themes(text):
            theme_counts[theme] = (
                theme_counts.get(theme, 0) + 1
            )

    theme_counts = dict(
        sorted(
            theme_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )
    )
    keywords = tfidf_keywords(
        disagreement_texts,
        top_n=top_n,
    )
    semantic_score = None

    if disagreement_texts and agreement_texts:
        semantic_score = semantic_similarity(
            disagreement_texts,
            agreement_texts,
        )

    topic_analysis = discover_topics(
        disagreement_texts,
        n_topics=8,
        top_words=10,
        min_df=2,
    )
    resolution_records = []

    for _, row in disagreements.iterrows():

        text = combine_resolution_text(
            row["resolution_title"],
            row["agenda_title"],
            row["subjects"],
        )

        resolution_records.append(
            {
                "resolution_id": int(
                    row["resolution_id"]
                ),

                "resolution_code": (
                    row["resolution_code"]
                ),

                "resolution_title": (
                    row["resolution_title"]
                ),

                "agenda_title": (
                    row["agenda_title"]
                ),

                "subjects": (
                    row["subjects"]
                ),

                "vote_a": row["vote_label_a"],
                "vote_b": row["vote_label_b"],

                "vote_score_a": (
                    float(row["vote_score_a"])
                ),

                "vote_score_b": (
                    float(row["vote_score_b"])
                ),

                # NLP thematic classification
                "themes": classify_text_themes(
                    text
                ),

                # Preserve provenance boundary
                "evidence_source": "UN_VOTING",
                "provenance": "UN_VOTES_ANALYZER",
            }
        )
    return {
        "pair": (
            f"{country_a.upper()}-"
            f"{country_b.upper()}"
        ),

        "disagreement_resolutions": len(
            disagreements
        ),

        "agreement_resolutions": len(
            agreements
        ),
        "themes": theme_counts,
        "keywords": keywords,
        "semantic_similarity": semantic_score,

        "topic_analysis": topic_analysis,

        "nlp_methodology": {
            "keyword_method": "TF_IDF",
            "similarity_method": "TF_IDF_COSINE",
            "topic_method": "NMF",
            "theme_method": "RULE_BASED",
        },
        "similarity_to_agreement": similarity,

        "resolutions": resolution_records,

        "evidence_source": "UN_VOTING",

        "provenance": "UN_VOTES_ANALYZER",

        # Future-compatible evidence boundary.
        "external_evidence": [],
    }


__all__ = [
    "pair_resolution_nlp",
]