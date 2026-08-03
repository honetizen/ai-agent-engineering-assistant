import base64

import httpx
from fastapi.testclient import TestClient

from app.api.pull_requests import get_github_client
from app.main import app
from app.services.github_client import GitHubClient


CONTEXT_PATH = "/github/repos/example/project/pulls/1/context"
GITHUB_METADATA = {
    "number": 1,
    "title": "Add project context",
    "state": "open",
    "merged": False,
    "user": {"login": "developer"},
    "base": {
        "ref": "main",
        "sha": "base-sha-123",
        "repo": {"full_name": "example/project"},
    },
    "head": {
        "ref": "feature/project-context",
        "sha": "head-sha-456",
        "repo": {"full_name": "example/project"},
    },
    "commits": 1,
    "changed_files": 0,
    "additions": 0,
    "deletions": 0,
    "html_url": "https://github.com/example/project/pull/1",
}


def encoded_file(content: str) -> httpx.Response:
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    return httpx.Response(
        200,
        json={"encoding": "base64", "content": encoded},
    )


def client_with_transport(transport: httpx.MockTransport) -> TestClient:
    app.dependency_overrides[get_github_client] = lambda: GitHubClient(
        token="test-token",
        transport=transport,
    )
    return TestClient(app)


def test_context_api_includes_project_context() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/pulls/1/files"):
            return httpx.Response(200, json=[])
        if path.endswith("/pulls/1"):
            return httpx.Response(200, json=GITHUB_METADATA)
        if path.endswith("/contents/README.md"):
            return encoded_file("# Project")
        if path.endswith("/contents/ARCHITECTURE.md"):
            return encoded_file("# Architecture")
        if path.endswith("/contents/CONTRIBUTING.md"):
            return httpx.Response(404, json={"message": "Not Found"})
        raise AssertionError(f"Unexpected GitHub path: {path}")

    with client_with_transport(httpx.MockTransport(handler)) as client:
        response = client.get(CONTEXT_PATH)
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["project_context"] == {
        "readme": "# Project",
        "architecture": "# Architecture",
        "contributing": None,
    }


def test_context_api_maps_github_404() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(404, json={"message": "Not Found"})
    )

    with client_with_transport(transport) as client:
        response = client.get(CONTEXT_PATH)
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Pull request not found"}


def test_context_api_maps_project_document_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/pulls/1/files"):
            return httpx.Response(200, json=[])
        if path.endswith("/pulls/1"):
            return httpx.Response(200, json=GITHUB_METADATA)
        raise httpx.ReadTimeout("GitHub timed out", request=request)

    with client_with_transport(httpx.MockTransport(handler)) as client:
        response = client.get(CONTEXT_PATH)
    app.dependency_overrides.clear()

    assert response.status_code == 504
    assert response.json() == {"detail": "GitHub request timed out"}
