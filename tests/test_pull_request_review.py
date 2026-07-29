import httpx
from fastapi.testclient import TestClient

from app.api.pull_requests import get_github_client
from app.main import app
from app.services.github_client import GitHubClient


REVIEW_PATH = "/github/repos/honetizen/ai-agent-engineering-assistant/pulls/1/review"


def client_with_transport(transport: httpx.MockTransport) -> TestClient:
    app.dependency_overrides[get_github_client] = lambda: GitHubClient(
        token="test-token",
        transport=transport,
    )
    return TestClient(app)


def test_pull_request_review_returns_structured_report() -> None:
    github_files = [
        {
            "filename": "app/service.py",
            "status": "modified",
            "additions": 4,
            "deletions": 1,
            "changes": 5,
            "patch": "@@ -1 +1,4 @@",
        }
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/pulls/1/files")
        return httpx.Response(200, json=github_files)

    with client_with_transport(httpx.MockTransport(handler)) as client:
        response = client.get(REVIEW_PATH)
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "risk_level": "medium",
        "findings": [
            {
                "rule_id": "missing_tests",
                "severity": "medium",
                "message": (
                    "Python business files changed without Python test changes."
                ),
                "filename": None,
            }
        ],
        "files_reviewed": 1,
    }


def test_pull_request_review_maps_github_404() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(404, json={"message": "Not Found"})
    )

    with client_with_transport(transport) as client:
        response = client.get(REVIEW_PATH)
    app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json() == {"detail": "Pull request not found"}


def test_pull_request_review_maps_github_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("GitHub timed out", request=request)

    with client_with_transport(httpx.MockTransport(handler)) as client:
        response = client.get(REVIEW_PATH)
    app.dependency_overrides.clear()

    assert response.status_code == 504
    assert response.json() == {"detail": "GitHub request timed out"}
