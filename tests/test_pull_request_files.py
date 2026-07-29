import httpx
from fastapi.testclient import TestClient

from app.api.pull_requests import get_github_client
from app.main import app
from app.services.github_client import GitHubClient


FILES_PATH = "/github/repos/honetizen/ai-agent-engineering-assistant/pulls/1/files"
GITHUB_FILES = [
    {
        "sha": "abc123",
        "filename": "app/main.py",
        "status": "modified",
        "additions": 5,
        "deletions": 1,
        "changes": 6,
        "patch": "@@ -1,2 +1,6 @@",
        "raw_url": "https://github.example/raw",
    },
]


def client_with_transport(transport: httpx.MockTransport) -> TestClient:
    app.dependency_overrides[get_github_client] = lambda: GitHubClient(
        token="test-token",
        transport=transport,
    )
    return TestClient(app)


def test_get_pull_request_files_returns_structured_files() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/pulls/1/files")
        return httpx.Response(200, json=GITHUB_FILES)

    with client_with_transport(httpx.MockTransport(handler)) as client:
        response = client.get(FILES_PATH)
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == [
        {
            "filename": "app/main.py",
            "status": "modified",
            "additions": 5,
            "deletions": 1,
            "changes": 6,
            "patch": "@@ -1,2 +1,6 @@",
        },
    ]


def test_get_pull_request_files_handles_missing_patch() -> None:
    github_file_without_patch = {
        "sha": "def456",
        "filename": "assets/logo.png",
        "status": "added",
        "additions": 0,
        "deletions": 0,
        "changes": 0,
    }
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json=[github_file_without_patch])
    )

    with client_with_transport(transport) as client:
        response = client.get(FILES_PATH)
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == [
        {
            "filename": "assets/logo.png",
            "status": "added",
            "additions": 0,
            "deletions": 0,
            "changes": 0,
            "patch": None,
        }
    ]


def test_get_pull_request_files_maps_github_404() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(404, json={"message": "Not Found"})
    )

    with client_with_transport(transport) as client:
        response = client.get(FILES_PATH)
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Pull request not found"}


def test_get_pull_request_files_maps_github_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("GitHub timed out", request=request)

    with client_with_transport(httpx.MockTransport(handler)) as client:
        response = client.get(FILES_PATH)
    app.dependency_overrides.clear()

    assert response.status_code == 504
    assert response.json() == {"detail": "GitHub request timed out"}
