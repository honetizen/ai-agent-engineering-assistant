import httpx
from fastapi.testclient import TestClient

from app.api.pull_requests import get_github_client
from app.main import app
from app.services.github_client import GitHubClient


PR_PATH = "/github/repos/honetizen/ai-agent-engineering-assistant/pulls/1"
GITHUB_PR = {
    "number": 1,
    "title": "Add health check test",
    "state": "closed",
    "merged": True,
    "user": {"login": "honetizen"},
    "base": {"ref": "main"},
    "head": {"ref": "feature/health-check-test"},
    "commits": 1,
    "changed_files": 3,
    "additions": 19,
    "deletions": 1,
    "html_url": "https://github.com/honetizen/ai-agent-engineering-assistant/pull/1",
    "ignored_raw_field": "not exposed",
}


def client_with_transport(transport: httpx.MockTransport) -> TestClient:
    app.dependency_overrides[get_github_client] = lambda: GitHubClient(
        token="test-token",
        transport=transport,
    )
    return TestClient(app)


def test_get_pull_request_returns_structured_metadata() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Accept"] == "application/vnd.github+json"
        assert request.headers["X-GitHub-Api-Version"] == "2022-11-28"
        assert request.headers["User-Agent"] == "ai-github-engineering-assistant"
        assert request.headers["Authorization"] == "Bearer test-token"
        return httpx.Response(200, json=GITHUB_PR)

    with client_with_transport(httpx.MockTransport(handler)) as client:
        response = client.get(PR_PATH)
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "number": 1,
        "title": "Add health check test",
        "state": "closed",
        "merged": True,
        "author": "honetizen",
        "base_branch": "main",
        "head_branch": "feature/health-check-test",
        "commits": 1,
        "changed_files": 3,
        "additions": 19,
        "deletions": 1,
        "html_url": "https://github.com/honetizen/ai-agent-engineering-assistant/pull/1",
    }


def test_get_pull_request_maps_github_404() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(404, json={"message": "Not Found"})
    )

    with client_with_transport(transport) as client:
        response = client.get(PR_PATH)
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Pull request not found"}


def test_get_pull_request_maps_github_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("GitHub timed out", request=request)

    with client_with_transport(httpx.MockTransport(handler)) as client:
        response = client.get(PR_PATH)
    app.dependency_overrides.clear()

    assert response.status_code == 504
    assert response.json() == {"detail": "GitHub request timed out"}
