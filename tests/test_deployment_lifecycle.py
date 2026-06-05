import time

from fastapi.testclient import TestClient


def wait_until_ready(client: TestClient, deployment_id: str, timeout: float = 5.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        response = client.get(f"/deployments/{deployment_id}")
        assert response.status_code == 200
        body = response.json()
        if body["status"] == "ready":
            return body
        time.sleep(0.1)
    raise AssertionError("Deployment did not become ready in time")


def test_deployment_provisioning_to_ready_to_terminated(client: TestClient):
    create = client.post("/deployments", json={"model": "model-a"})
    assert create.status_code == 201
    payload = create.json()
    assert payload["status"] == "provisioning"
    deployment_id = payload["deployment_id"]

    ready = wait_until_ready(client, deployment_id)
    assert ready["endpoint_url"]
    assert ready["api_key"]

    delete = client.delete(f"/deployments/{deployment_id}")
    assert delete.status_code == 204

    terminated = client.get(f"/deployments/{deployment_id}")
    assert terminated.json()["status"] == "terminated"

    completion = client.post(
        f"/v1/{deployment_id}/completions",
        json={"prompt": "hello"},
        headers={"Authorization": f"Bearer {ready['api_key']}"},
    )
    assert completion.status_code == 409


def test_completion_rejects_wrong_api_key_and_invalid_key(client: TestClient):
    create = client.post("/deployments", json={"model": "model-b"})
    deployment_id = create.json()["deployment_id"]
    ready = wait_until_ready(client, deployment_id)
    api_key = ready["api_key"]

    invalid = client.post(
        f"/v1/{deployment_id}/completions",
        json={"prompt": "test"},
        headers={"Authorization": "Bearer not-a-real-key"},
    )
    assert invalid.status_code == 401

    other = client.post("/deployments", json={"model": "model-a"})
    other_ready = wait_until_ready(client, other.json()["deployment_id"])

    mismatch = client.post(
        f"/v1/{deployment_id}/completions",
        json={"prompt": "test"},
        headers={"Authorization": f"Bearer {other_ready['api_key']}"},
    )
    assert mismatch.status_code == 403

    ok = client.post(
        f"/v1/{deployment_id}/completions",
        json={"prompt": "test"},
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert ok.status_code == 200
    assert ok.json()["output"] == "mocked response"
