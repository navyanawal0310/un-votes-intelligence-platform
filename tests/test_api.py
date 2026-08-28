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

    assert data["intent"] == "SUBSTANTIVE_DISAGREEMENT"

    assert "disagreement" in (
        data["answer"].lower()
    )

    assert data["evidence_source"] == "UN_VOTING"
    assert data["provenance"] == "UN_VOTES_ANALYZER"
    assert data["evidence"] is not None

    assert "temporal_alignment" in data["evidence"]
    assert "change_points" in data["evidence"]
    assert "issue_attribution" in data["evidence"]
    assert "episode_attribution" in data["evidence"]
    
    assert data["evidence"]["temporal_alignment"] == 43
    assert data["evidence"] is not None
    assert isinstance(data["evidence"], dict)