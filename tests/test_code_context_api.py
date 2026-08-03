import base64

import httpx
from fastapi.testclient import TestClient

from app.api.pull_requests import get_github_client
from app.main import app
from app.services.github_client import GitHubClient


CONTEXT_PATH = "/github/repos/example/project/pulls/1/context"
GITHUB_METADATA = {
    "number": 1,
    "title": "Add code context",
    "state": "open",
    "merged": False,
    "user": {"login": "developer"},
    "base": {
        "ref": "main",
        "sha": "base-sha-123",
        "repo": {"full_name": "example/project"},
    },
    "head": {
        "ref": "feature/code-context",
        "sha": "head-sha-456",
        "repo": {"full_name": "example/project"},
    },
    "commits": 1,
    "changed_files": 1,
    "additions": 1,
    "deletions": 0,
    "html_url": "https://github.com/example/project/pull/1",
}
GITHUB_FILES = [
    {
        "filename": "app/login.py",
        "status": "modified",
        "additions": 1,
        "deletions": 0,
        "changes": 1,
        "patch": "@@ -1 +1 @@",
    }
]


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


def test_context_api_includes_code_context() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/pulls/1/files"):
            return httpx.Response(200, json=GITHUB_FILES)
        if path.endswith("/pulls/1"):
            return httpx.Response(200, json=GITHUB_METADATA)
        if path.endswith("/contents/app/login.py"):
            return encoded_file("def login(): ...")
        if path.endswith("/contents/tests/test_login.py"):
            return encoded_file("def test_login(): ...")
        if "/contents/" in path:
            return httpx.Response(404, json={"message": "Not Found"})
        raise AssertionError(f"Unexpected GitHub path: {path}")

    with client_with_transport(httpx.MockTransport(handler)) as client:
        response = client.get(CONTEXT_PATH)
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["code_context"] == {
        "changed_file_contents": {
            "app/login.py": "def login(): ..."
        },
        "related_test_contents": {
            "tests/test_login.py": "def test_login(): ..."
        },
    }


def test_context_api_maps_code_content_github_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/pulls/1/files"):
            return httpx.Response(200, json=GITHUB_FILES)
        if path.endswith("/pulls/1"):
            return httpx.Response(200, json=GITHUB_METADATA)
        if path.endswith("/contents/app/login.py"):
            return httpx.Response(
                500,
                json={"message": "Internal Server Error"},
            )
        if "/contents/" in path:
            return httpx.Response(404, json={"message": "Not Found"})
        raise AssertionError(f"Unexpected GitHub path: {path}")

    with client_with_transport(httpx.MockTransport(handler)) as client:
        response = client.get(CONTEXT_PATH)
    app.dependency_overrides.clear()

    assert response.status_code == 502
    assert response.json() == {"detail": "GitHub request failed"}
