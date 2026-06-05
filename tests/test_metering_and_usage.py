from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from tests.test_deployment_lifecycle import wait_until_ready


@patch("app.services.completion_service.random.randint", return_value=100)
def test_usage_aggregation_matches_recorded_completions(
    _mock_randint: object,
    client: TestClient,
):
    create = client.post("/deployments", json={"model": "model-a"})
    deployment_id = create.json()["deployment_id"]
    ready = wait_until_ready(client, deployment_id)
    api_key = ready["api_key"]
    headers = {"Authorization": f"Bearer {api_key}"}

    prompts = ["abcd", "abcdefgh"]  # input_tokens: 1 and 2
    for prompt in prompts:
        response = client.post(
            f"/v1/{deployment_id}/completions",
            json={"prompt": prompt},
            headers=headers,
        )
        assert response.status_code == 200

    now = datetime.now(timezone.utc)
    usage = client.get(
        "/usage",
        params={
            "api_key": api_key,
            "from": (now - timedelta(hours=1)).isoformat(),
            "to": (now + timedelta(hours=1)).isoformat(),
            "group_by": "model",
        },
    )
    assert usage.status_code == 200
    body = usage.json()

    assert body["total_input_tokens"] == 3
    assert body["total_output_tokens"] == 200
    assert body["total_tokens"] == 203
    assert body["groups"][0]["group_key"] == "model-a"
    assert body["groups"][0]["input_tokens"] == 3
    assert body["groups"][0]["output_tokens"] == 200

    expected_cost = (3 / 1000) * 0.001 + (200 / 1000) * 0.002
    assert abs(body["total_cost"] - round(expected_cost, 6)) < 1e-9


def test_rate_limit_returns_429(client: TestClient):
    from app.config import settings

    create = client.post("/deployments", json={"model": "model-a"})
    ready = wait_until_ready(client, create.json()["deployment_id"])
    headers = {"Authorization": f"Bearer {ready['api_key']}"}
    deployment_id = create.json()["deployment_id"]

    limit = settings.rate_limit_per_minute
    for _ in range(limit):
        assert (
            client.post(
                f"/v1/{deployment_id}/completions",
                json={"prompt": "x"},
                headers=headers,
            ).status_code
            == 200
        )

    blocked = client.post(
        f"/v1/{deployment_id}/completions",
        json={"prompt": "x"},
        headers=headers,
    )
    assert blocked.status_code == 429
