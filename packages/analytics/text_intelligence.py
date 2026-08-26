"""
Text intelligence layer for UN resolution evidence.

Provides source-agnostic NLP features over UN resolution text.

Current methods:
- text normalization
- UN-domain stopword filtering
- TF-IDF keyword extraction
- subject-specific keyword extraction
- cosine similarity
- transparent thematic classification
- resolution text comparison

Future-compatible with:
- embeddings
- transformer models
- speeches
- geopolitical event text
- current-affairs evidence
"""

from __future__ import annotations

import re
from typing import Any

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ---------------------------------------------------------------------------
# UN-domain boilerplate
# ---------------------------------------------------------------------------

UN_DOMAIN_STOPWORDS = {
    "general",
    "assembly",
    "resolution",
    "resolutions",
    "adopted",
    "adopt",
    "session",
    "agenda",
    "question",
    "considered",
    "decision",
    "decides",
    "document",
    "documents",
    "report",
    "reports",
    "committee",
    "meeting",
    "meetings",
    "draft",
    "drafts",
    "paragraph",
    "paragraphs",
    "article",
    "articles",
    "international",
}


# ---------------------------------------------------------------------------
# Text normalization
# ---------------------------------------------------------------------------

def normalize_text(value: Any) -> str:
    """Normalize arbitrary text into a clean NLP-ready string."""

    if value is None or pd.isna(value):
        return ""

    text = str(value).lower()

    text = re.sub(
        r"https?://\S+",
        " ",
        text,
    )

    text = re.sub(
        r"[^a-z0-9\s\-]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ---------------------------------------------------------------------------
# Resolution text construction
# ---------------------------------------------------------------------------

def combine_resolution_text(
    resolution_title: Any,
    agenda_title: Any = None,
    subjects: Any = None,
) -> str:
    """Combine available UN resolution metadata into one NLP document."""

    parts = [
        normalize_text(resolution_title),
        normalize_text(agenda_title),
        normalize_text(subjects),
    ]

    return " ".join(
        part for part in parts if part
    )


# ---------------------------------------------------------------------------
# Stopword configuration
# ---------------------------------------------------------------------------

def _stopwords() -> list[str]:
    """Return English + UN-domain stopwords."""

    english_stopwords = (
        TfidfVectorizer(
            stop_words="english"
        ).get_stop_words()
    )

    return list(
        set(english_stopwords)
        | UN_DOMAIN_STOPWORDS
    )


# ---------------------------------------------------------------------------
# TF-IDF
# ---------------------------------------------------------------------------

def tfidf_keywords(
    texts: list[str],
    top_n: int = 20,
    min_df: int = 1,
) -> list[dict[str, Any]]:
    """
    Extract globally important TF-IDF terms.

    UN procedural/document boilerplate is removed before
    ranking terms.

    Returns terms ranked by aggregate TF-IDF weight.
    """

    cleaned = [
        normalize_text(text)
        for text in texts
    ]

    cleaned = [
        text
        for text in cleaned
        if text
    ]

    if not cleaned:
        return []

    vectorizer = TfidfVectorizer(
        stop_words=_stopwords(),
        ngram_range=(1, 2),
        min_df=min_df,
        max_df=0.90,
    )

    matrix = vectorizer.fit_transform(
        cleaned
    )

    scores = matrix.sum(
        axis=0
    ).A1

    terms = vectorizer.get_feature_names_out()

    ranked = sorted(
        zip(terms, scores),
        key=lambda x: x[1],
        reverse=True,
    )

    return [
        {
            "term": term,
            "score": float(score),
        }
        for term, score in ranked[:top_n]
    ]


# ---------------------------------------------------------------------------
# Subject-specific NLP
# ---------------------------------------------------------------------------

def extract_subject_keywords(
    resolutions: pd.DataFrame,
    top_n: int = 20,
) -> list[dict[str, Any]]:
    """
    Extract TF-IDF keywords specifically from
    UN subject metadata.
    """

    if resolutions.empty:
        return []

    if "subjects" not in resolutions.columns:
        return []

    subjects = [
        normalize_text(value)
        for value in resolutions["subjects"]
        if value is not None
        and not pd.isna(value)
    ]

    subjects = [
        value
        for value in subjects
        if value
    ]

    if not subjects:
        return []

    return tfidf_keywords(
        subjects,
        top_n=top_n,
    )


# ---------------------------------------------------------------------------
# Transparent thematic classification
# ---------------------------------------------------------------------------

def classify_text_themes(
    text: str,
) -> list[str]:
    """
    Lightweight transparent thematic classification.

    This is intentionally interpretable.

    It can later be replaced or supplemented by:
    - embeddings
    - transformer classifiers
    - topic models
    """

    text = normalize_text(text)

    theme_terms = {
        "disarmament": [
            "nuclear",
            "disarmament",
            "weapon",
            "weapons",
            "arms",
            "missile",
            "non proliferation",
            "non-proliferation",
            "proliferation",
        ],

        "human_rights": [
            "human rights",
            "rights",
            "freedom",
            "refugee",
            "refugees",
            "discrimination",
            "torture",
        ],

        "peace_security": [
            "peace",
            "security",
            "conflict",
            "war",
            "ceasefire",
            "peacekeeping",
        ],

        "development": [
            "development",
            "economic",
            "economy",
            "poverty",
            "trade",
            "sustainable",
            "development goals",
        ],

        "environment": [
            "climate",
            "environment",
            "pollution",
            "biodiversity",
            "environmental",
        ],

        "decolonization": [
            "colonial",
            "colonialism",
            "decolonization",
            "self determination",
            "self-determination",
            "territory",
            "occupation",
        ],

        "palestine_middle_east": [
            "palestine",
            "palestinian",
            "israel",
            "israeli",
            "gaza",
            "middle east",
            "jerusalem",
        ],
    }

    themes: list[str] = []

    for theme, terms in theme_terms.items():
        if any(
            term in text
            for term in terms
        ):
            themes.append(theme)

    return themes


# ---------------------------------------------------------------------------
# Text similarity
# ---------------------------------------------------------------------------

def text_similarity(
    text_a: str,
    text_b: str,
) -> float | None:
    """Calculate cosine similarity between two text documents."""

    a = normalize_text(text_a)
    b = normalize_text(text_b)

    if not a or not b:
        return None

    vectorizer = TfidfVectorizer(
        stop_words=_stopwords(),
        ngram_range=(1, 2),
    )

    matrix = vectorizer.fit_transform(
        [a, b]
    )

    return float(
        cosine_similarity(
            matrix[0:1],
            matrix[1:2],
        )[0, 0]
    )


# ---------------------------------------------------------------------------
# Resolution feature extraction
# ---------------------------------------------------------------------------

def resolution_text_features(
    resolutions: pd.DataFrame,
    top_n: int = 20,
) -> dict[str, Any]:
    """
    Generate NLP features from a resolution dataframe.

    Expected columns:
        resolution_title
        agenda_title
        subjects
    """

    if resolutions.empty:
        return {
            "documents": 0,
            "keywords": [],
            "subject_keywords": [],
            "themes": {},
        }

    required = {
        "resolution_title",
        "agenda_title",
        "subjects",
    }

    missing = required - set(
        resolutions.columns
    )

    if missing:
        raise ValueError(
            "Missing resolution text columns: "
            f"{sorted(missing)}"
        )

    texts = [
        combine_resolution_text(
            row["resolution_title"],
            row["agenda_title"],
            row["subjects"],
        )
        for _, row in resolutions.iterrows()
    ]

    theme_counts: dict[str, int] = {}

    for text in texts:
        for theme in classify_text_themes(text):
            theme_counts[theme] = (
                theme_counts.get(theme, 0) + 1
            )

    return {
        "documents": len(texts),

        "keywords": tfidf_keywords(
            texts,
            top_n=top_n,
        ),

        "subject_keywords": extract_subject_keywords(
            resolutions,
            top_n=top_n,
        ),

        "themes": dict(
            sorted(
                theme_counts.items(),
                key=lambda x: x[1],
                reverse=True,
            )
        ),
    }


# ---------------------------------------------------------------------------
# Corpus comparison
# ---------------------------------------------------------------------------

def compare_resolution_corpora(
    corpus_a: list[str],
    corpus_b: list[str],
) -> dict[str, Any]:
    """
    Compare two country-associated resolution corpora.

    This is deliberately country-agnostic.
    """

    texts_a = [
        normalize_text(x)
        for x in corpus_a
        if normalize_text(x)
    ]

    texts_b = [
        normalize_text(x)
        for x in corpus_b
        if normalize_text(x)
    ]

    if not texts_a or not texts_b:
        return {
            "similarity": None,
            "keywords_a": [],
            "keywords_b": [],
        }

    return {
        "similarity": text_similarity(
            " ".join(texts_a),
            " ".join(texts_b),
        ),

        "keywords_a": tfidf_keywords(
            texts_a,
            top_n=15,
        ),

        "keywords_b": tfidf_keywords(
            texts_b,
            top_n=15,
        ),
    }


__all__ = [
    "normalize_text",
    "combine_resolution_text",
    "tfidf_keywords",
    "extract_subject_keywords",
    "classify_text_themes",
    "text_similarity",
    "resolution_text_features",
    "compare_resolution_corpora",
]