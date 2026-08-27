from packages.analytics.answer_generation import (
    generate_answer,
    generate_relationship_answer,
)


def test_relationship_answer_contains_score():
    result = {
        "pair": "IND-CHN",
        "relationship_direction": "ALIGNED",
        "relationship_score": 0.892708,
        "alignment": 0.927083,
        "divergence": 0.145833,
        "latest_year": 2025,
        "evidence_count": 192,
    }

    answer = generate_relationship_answer(
        result
    )

    assert "IND-CHN" in answer
    assert "0.893" in answer
    assert "ALIGNED" in answer
    assert "2025" in answer


def test_generate_answer_relationship():
    result = {
        "pair": "IND-CHN",
        "relationship_direction": "ALIGNED",
        "relationship_score": 0.892708,
        "alignment": 0.927083,
        "divergence": 0.145833,
        "latest_year": 2025,
        "evidence_count": 192,
    }

    answer = generate_answer(
        "RELATIONSHIP_PROFILE",
        result,
    )

    assert isinstance(answer, str)
    assert "relationship" in answer.lower()
    assert "0.893" in answer

def test_execute_query_contains_natural_language_answer():
    from packages.analytics.query import execute_query

    result = execute_query(
        "How aligned are India and China?",
        "India",
        "China",
    )

    assert "answer" in result
    assert isinstance(result["answer"], str)
    assert len(result["answer"]) > 50

    assert "0.893" in result["answer"]
    assert "ALIGNED" in result["answer"]

    assert result["evidence_source"] == "UN_VOTING"
    assert result["provenance"] == "UN_VOTES_ANALYZER"

def test_substantive_answer_does_not_dump_dataframe():
    import pandas as pd

    from packages.analytics.answer_generation import (
        generate_substantive_answer,
    )

    disagreements = pd.DataFrame(
        {
            "resolution_id": [1, 2, 3],
            "resolution_code": [
                "A/RES/1",
                "A/RES/2",
                "A/RES/3",
            ],
        }
    )

    result = {
        "pair": "IND-CHN",
        "resolution_disagreements": disagreements,
        "subject_rankings": pd.DataFrame(
            {
                "subject": [
                    "DISARMAMENT",
                    "HUMAN RIGHTS",
                ],
                "disagreement_percentage": [
                    80.0,
                    60.0,
                ],
            }
        ),
        "evidence_summary": {
            "subjects": 153,
            "resolution_disagreements": disagreements,
        },
    }

    answer = generate_substantive_answer(
        result
    )

    assert "Resolution-level disagreements: 3." in answer
    assert "DISARMAMENT: 80.00% disagreement" in answer
    assert "[3 rows x" not in answer

def test_history_answer():
    import pandas as pd

    from packages.analytics.answer_generation import (
        generate_answer,
    )

    result = pd.DataFrame(
        {
            "year": [1946, 2025],
            "relationship_score": [
                0.663462,
                0.892708,
            ],
        }
    )

    answer = generate_answer(
        "RELATIONSHIP_HISTORY",
        result,
    )

    assert "1946" in answer
    assert "2025" in answer
    assert "0.663" in answer
    assert "0.893" in answer


def test_changes_answer():
    import pandas as pd

    from packages.analytics.answer_generation import (
        generate_answer,
    )

    result = pd.DataFrame(
        {
            "change_year": [1960, 1975],
        }
    )

    answer = generate_answer(
        "RELATIONSHIP_CHANGES",
        result,
    )

    assert "2 relationship change points" in answer
    assert "1960" in answer
    assert "1975" in answer


def test_subject_ranking_answer():
    import pandas as pd

    from packages.analytics.answer_generation import (
        generate_answer,
    )

    result = {
        "subject_rankings": pd.DataFrame(
            {
                "subject": [
                    "DISARMAMENT",
                    "HUMAN RIGHTS",
                ],
                "disagreement_percentage": [
                    90.0,
                    75.0,
                ],
            }
        )
    }

    answer = generate_answer(
        "SUBJECT_RANKING",
        result,
    )

    assert "DISARMAMENT" in answer
    assert "90.00%" in answer


def test_subject_trend_answer():
    import pandas as pd

    from packages.analytics.answer_generation import (
        generate_answer,
    )

    result = pd.DataFrame(
        {
            "year": [1980, 1981, 1982],
            "subject": [
                "DISARMAMENT",
                "DISARMAMENT",
                "HUMAN RIGHTS",
            ],
        }
    )

    answer = generate_answer(
        "SUBJECT_TREND",
        result,
    )

    assert "3 observations" in answer
    assert "1980" in answer
    assert "1982" in answer


def test_issue_position_answer():
    import pandas as pd

    from packages.analytics.answer_generation import (
        generate_answer,
    )

    result = {
        "IND": pd.DataFrame({"issue": ["A", "B"]}),
        "CHN": pd.DataFrame({"issue": ["A"]}),
    }

    answer = generate_answer(
        "ISSUE_POSITION",
        result,
    )

    assert "IND" in answer
    assert "CHN" in answer


def test_resolution_nlp_answer():
    result = {
        "disagreement_resolutions": 1009,
        "similarity_to_agreement": 0.617,
        "keywords": [
            {"term": "nuclear", "score": 50.0},
            {"term": "disarmament", "score": 40.0},
        ],
    }

    from packages.analytics.answer_generation import (
        generate_answer,
    )

    answer = generate_answer(
        "RESOLUTION_NLP",
        result,
    )

    assert "1009" in answer
    assert "0.617" in answer
    assert "nuclear" in answer
