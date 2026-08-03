import httpx
from fastapi.testclient import TestClient

from app.api.pull_requests import get_github_client
from app.main import app
from app.services.github_client import GitHubClient


AI_REVIEW_PATH = "/github/repos/example/project/pulls/1/ai-review"
GITHUB_METADATA = {
    "number": 1,
    "title": "Add AI review skeleton",
    "state": "open",
    "merged": False,
    "user": {"login": "developer"},
    "base": {"ref": "main"},
    "head": {"ref": "feature/ai-review"},
    "commits": 1,
    "changed_files": 0,
    "additions": 0,
    "deletions": 0,
    "html_url": "https://github.com/example/project/pull/1",
}


def client_with_transport(transport: httpx.MockTransport) -> TestClient:
    app.dependency_overrides[get_github_client] = lambda: GitHubClient(
        token="test-token",
        transport=transport,
    )
    return TestClient(app)


def test_ai_review_api_returns_mock_report() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/pulls/1/files"):
            return httpx.Response(200, json=[])
        if path.endswith("/pulls/1"):
            return httpx.Response(200, json=GITHUB_METADATA)
        if "/contents/" in path:
            return httpx.Response(404, json={"message": "Not Found"})
        raise AssertionError(f"Unexpected GitHub path: {path}")

    with client_with_transport(httpx.MockTransport(handler)) as client:
        response = client.get(AI_REVIEW_PATH)
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "summary": "Mock AI review completed",
        "findings": [],
    }


def test_ai_review_api_maps_context_not_found() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(404, json={"message": "Not Found"})
    )

    with client_with_transport(transport) as client:
        response = client.get(AI_REVIEW_PATH)
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Pull request not found"}


def test_ai_review_api_maps_github_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("GitHub timed out", request=request)

    with client_with_transport(httpx.MockTransport(handler)) as client:
        response = client.get(AI_REVIEW_PATH)
    app.dependency_overrides.clear()

    assert response.status_code == 504
    assert response.json() == {"detail": "GitHub request timed out"}


def test_ai_review_api_maps_github_upstream_error() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            500,
            json={"message": "Internal Server Error"},
        )
    )

    with client_with_transport(transport) as client:
        response = client.get(AI_REVIEW_PATH)
    app.dependency_overrides.clear()

    assert response.status_code == 502
    assert response.json() == {"detail": "GitHub request failed"}
