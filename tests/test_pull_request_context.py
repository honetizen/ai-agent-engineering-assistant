import httpx
from fastapi.testclient import TestClient

from app.api.pull_requests import get_github_client
from app.main import app
from app.services.github_client import GitHubClient


CONTEXT_PATH = (
    "/github/repos/honetizen/ai-agent-engineering-assistant/pulls/1/context"
)
GITHUB_METADATA = {
    "number": 1,
    "title": "Add review context",
    "state": "open",
    "merged": False,
    "user": {"login": "honetizen"},
    "base": {"ref": "main"},
    "head": {"ref": "feature/review-context"},
    "commits": 1,
    "changed_files": 1,
    "additions": 4,
    "deletions": 1,
    "html_url": "https://github.com/example/project/pull/1",
}
GITHUB_FILES = [
    {
        "filename": "app/service.py",
        "status": "modified",
        "additions": 4,
        "deletions": 1,
        "changes": 5,
        "patch": "@@ -1 +1,4 @@",
    }
]


def client_with_transport(transport: httpx.MockTransport) -> TestClient:
    app.dependency_overrides[get_github_client] = lambda: GitHubClient(
        token="test-token",
        transport=transport,
    )
    return TestClient(app)


def test_pull_request_context_returns_complete_context() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/pulls/1/files"):
            return httpx.Response(200, json=GITHUB_FILES)
        if request.url.path.endswith("/pulls/1"):
            return httpx.Response(200, json=GITHUB_METADATA)
        if "/contents/" in request.url.path:
            return httpx.Response(404, json={"message": "Not Found"})
        raise AssertionError(f"Unexpected GitHub path: {request.url.path}")

    with client_with_transport(httpx.MockTransport(handler)) as client:
        response = client.get(CONTEXT_PATH)
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "pull_request": {
            "number": 1,
            "title": "Add review context",
            "state": "open",
            "merged": False,
            "author": "honetizen",
            "base_branch": "main",
            "head_branch": "feature/review-context",
            "commits": 1,
            "changed_files": 1,
            "additions": 4,
            "deletions": 1,
            "html_url": "https://github.com/example/project/pull/1",
        },
        "changed_files": [
            {
                "filename": "app/service.py",
                "status": "modified",
                "additions": 4,
                "deletions": 1,
                "changes": 5,
                "patch": "@@ -1 +1,4 @@",
            }
        ],
        "rule_report": {
            "risk_level": "medium",
            "findings": [
                {
                    "rule_id": "missing_tests",
                    "severity": "medium",
                    "message": (
                        "Python business files changed without "
                        "Python test changes."
                    ),
                    "filename": None,
                }
            ],
            "files_reviewed": 1,
        },
        "project_context": {
            "readme": None,
            "architecture": None,
            "contributing": None,
        },
    }


def test_pull_request_context_maps_metadata_404() -> None:
    request_paths = []

    def handler(request: httpx.Request) -> httpx.Response:
        request_paths.append(request.url.path)
        return httpx.Response(404, json={"message": "Not Found"})

    with client_with_transport(httpx.MockTransport(handler)) as client:
        response = client.get(CONTEXT_PATH)
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Pull request not found"}
    assert len(request_paths) == 1
    assert request_paths[0].endswith("/pulls/1")


def test_pull_request_context_maps_files_404() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/pulls/1/files"):
            return httpx.Response(404, json={"message": "Not Found"})
        return httpx.Response(200, json=GITHUB_METADATA)

    with client_with_transport(httpx.MockTransport(handler)) as client:
        response = client.get(CONTEXT_PATH)
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Pull request not found"}


def test_pull_request_context_maps_github_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("GitHub timed out", request=request)

    with client_with_transport(httpx.MockTransport(handler)) as client:
        response = client.get(CONTEXT_PATH)
    app.dependency_overrides.clear()

    assert response.status_code == 504
    assert response.json() == {"detail": "GitHub request timed out"}
