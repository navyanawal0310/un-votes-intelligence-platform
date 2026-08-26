"""
Semantic NLP foundation for UN resolution evidence.

Provides interpretable semantic representations and topic discovery
over resolution text.

This module is source-agnostic and does not fetch external data.

Future-compatible with:
- transformer embeddings
- sentence embeddings
- speeches
- geopolitical events
- current-affairs documents
"""

from __future__ import annotations

from typing import Any

import pandas as pd
import numpy as np
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def build_tfidf_matrix(
    texts: list[str],
    min_df: int = 2,
    max_df: float = 0.95,
) -> tuple[Any, Any]:
    """
    Build an interpretable TF-IDF semantic representation.

    Returns:
        vectorizer, matrix
    """

    cleaned = [
        str(text).strip()
        for text in texts
        if text and str(text).strip()
    ]

    if not cleaned:
        raise ValueError("No usable text supplied.")

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        min_df=min_df,
        max_df=max_df,
        sublinear_tf=True,
    )

    matrix = vectorizer.fit_transform(cleaned)

    return vectorizer, matrix


def semantic_similarity(
    texts_a: list[str],
    texts_b: list[str],
) -> float | None:
    """
    Compare two text corpora using TF-IDF semantic representation.

    This is deliberately interpretable and acts as the baseline
    for future transformer-based embeddings.
    """

    a = [
        str(x).strip()
        for x in texts_a
        if x and str(x).strip()
    ]

    b = [
        str(x).strip()
        for x in texts_b
        if x and str(x).strip()
    ]

    if not a or not b:
        return None

    corpus = a + b

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        sublinear_tf=True,
    )

    matrix = vectorizer.fit_transform(corpus)

    centroid_a = np.asarray(
        matrix[: len(a)].mean(axis=0)
    )

    centroid_b = np.asarray(
        matrix[len(a) :].mean(axis=0)
    )

    return float(
        cosine_similarity(
            centroid_a,
            centroid_b,
        )[0, 0]
    )

def discover_topics(
    texts: list[str],
    n_topics: int = 8,
    top_words: int = 10,
    min_df: int = 2,
) -> dict[str, Any]:
    """
    Discover latent topics using NMF over TF-IDF features.

    NMF provides an interpretable topic-model baseline.
    """

    cleaned = [
        str(text).strip()
        for text in texts
        if text and str(text).strip()
    ]

    if len(cleaned) < 3:
        return {
            "documents": len(cleaned),
            "topics": [],
        }

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        min_df=min_df,
        max_df=0.95,
    )

    matrix = vectorizer.fit_transform(cleaned)

    if matrix.shape[1] == 0:
        return {
            "documents": len(cleaned),
            "topics": [],
        }

    actual_topics = min(
        n_topics,
        matrix.shape[0],
        matrix.shape[1],
    )

    if actual_topics < 1:
        return {
            "documents": len(cleaned),
            "topics": [],
        }

    model = NMF(
        n_components=actual_topics,
        init="nndsvda",
        random_state=42,
        max_iter=500,
    )

    model.fit(matrix)

    terms = vectorizer.get_feature_names_out()

    topics = []

    for topic_index, component in enumerate(
        model.components_
    ):
        indices = component.argsort()[
            ::-1
        ][:top_words]

        topics.append(
            {
                "topic_id": topic_index,
                "keywords": [
                    {
                        "term": terms[i],
                        "weight": float(
                            component[i]
                        ),
                    }
                    for i in indices
                ],
            }
        )

    return {
        "documents": len(cleaned),
        "topics": topics,
    }


def document_topic_assignments(
    texts: list[str],
    n_topics: int = 8,
) -> list[dict[str, Any]]:
    """
    Assign each document to its dominant discovered topic.
    """

    cleaned = [
        str(text).strip()
        for text in texts
        if text and str(text).strip()
    ]

    if len(cleaned) < 3:
        return []

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
    )

    matrix = vectorizer.fit_transform(cleaned)

    actual_topics = min(
        n_topics,
        matrix.shape[0],
        matrix.shape[1],
    )

    if actual_topics < 1:
        return []

    model = NMF(
        n_components=actual_topics,
        init="nndsvda",
        random_state=42,
        max_iter=500,
    )

    document_topics = model.fit_transform(
        matrix
    )

    assignments = []

    for index, values in enumerate(
        document_topics
    ):
        topic_id = int(
            values.argmax()
        )

        assignments.append(
            {
                "document_index": index,
                "topic_id": topic_id,
                "topic_score": float(
                    values[topic_id]
                ),
            }
        )

    return assignments


__all__ = [
    "build_tfidf_matrix",
    "semantic_similarity",
    "discover_topics",
    "document_topic_assignments",
]