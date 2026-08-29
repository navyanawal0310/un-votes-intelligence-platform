from fastapi.testclient import TestClient

from packages.api.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["service"] == "un-votes-intelligence-platform"
    assert data["version"] == "1.0.0"


def test_relationship_endpoint():
    response = client.get(
        "/api/v1/relationship/IND/CHN"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["pair"] == "IND-CHN"
    assert data["country_a"] == "IND"
    assert data["country_b"] == "CHN"

    assert data["relationship_score"] is not None
    assert data["relationship_direction"] == "ALIGNED"

    assert data["evidence_source"] == "UN_VOTING"
    assert data["provenance"] == "UN_VOTES_ANALYZER"


def test_query_relationship():
    response = client.post(
        "/api/v1/query",
        json={
            "question": "How aligned are India and China?",
            "country_a": "IND",
            "country_b": "CHN",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["intent"] == "RELATIONSHIP_PROFILE"
    assert data["evidence_source"] == "UN_VOTING"
    assert data["provenance"] == "UN_VOTES_ANALYZER"

    assert "relationship" in data["answer"].lower()


def test_query_substantive_disagreement():
    response = client.post(
        "/api/v1/query",
        json={
            "question": "Why do India and China disagree?",
            "country_a": "IND",
            "country_b": "CHN",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["evidence"] is not None
    assert isinstance(data["evidence"], dict)
    assert "subjects" in data["evidence"]
    assert "subject_trend_rows" in data["evidence"]
    assert "resolution_disagreements" in data["evidence"]
    assert "issue_rows_country_a" in data["evidence"]
    assert "issue_rows_country_b" in data["evidence"]

    assert data["evidence"]["resolution_disagreements"] == 1412

def test_relationship_invalid_country():
    response = client.get(
        "/api/v1/relationship/XXX/CHN"
    )

    assert response.status_code in (400, 404)


def test_relationship_missing_country():
    response = client.get(
        "/api/v1/relationship/IND/"
    )

    assert response.status_code in (404, 405)


def test_query_empty_question():
    response = client.post(
        "/api/v1/query",
        json={
            "question": "",
            "country_a": "IND",
            "country_b": "CHN",
        },
    )

    assert response.status_code == 422


def test_query_missing_question():
    response = client.post(
        "/api/v1/query",
        json={
            "country_a": "IND",
            "country_b": "CHN",
        },
    )

    assert response.status_code == 422