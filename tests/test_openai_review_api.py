import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.pull_requests import get_github_client
from app.exceptions.ai_provider import (
    AIProviderConfigurationError,
    AIProviderError,
    AIProviderResponseError,
    AIProviderTimeoutError,
)
from app.main import app
from app.schemas.ai_prompt import AIReviewPrompt
from app.schemas.ai_review import AIReviewFinding, AIReviewReport
from app.services.github_client import GitHubClient


PATH = "/github/repos/example/project/pulls/1/ai-review/openai"
METADATA = {
    "number": 1, "title": "Review", "state": "open", "merged": False,
    "user": {"login": "developer"},
    "base": {"ref": "main", "sha": "base-sha", "repo": {"full_name": "example/project"}},
    "head": {"ref": "feature", "sha": "head-sha", "repo": {"full_name": "example/project"}},
    "commits": 1, "changed_files": 0, "additions": 0, "deletions": 0,
    "html_url": "https://github.com/example/project/pull/1",
}


class FakeProvider:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.prompt: AIReviewPrompt | None = None

    async def review(self, prompt: AIReviewPrompt) -> AIReviewReport:
        self.prompt = prompt
        if self.error is not None:
            raise self.error
        return AIReviewReport(
            summary="OpenAI review completed",
            findings=[AIReviewFinding(
                level="high", file="app/auth.py", line=12,
                issue="Unsafe behavior", suggestion="Validate input",
            )],
        )


def github_client() -> GitHubClient:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/pulls/1/files"):
            return httpx.Response(200, json=[])
        if request.url.path.endswith("/pulls/1"):
            return httpx.Response(200, json=METADATA)
        if "/contents/" in request.url.path:
            return httpx.Response(404, json={"message": "Not Found"})
        raise AssertionError(f"Unexpected request: {request.url}")

    return GitHubClient(token="test-token", transport=httpx.MockTransport(handler))


def post_with_provider(monkeypatch: pytest.MonkeyPatch, provider: FakeProvider):
    app.dependency_overrides[get_github_client] = github_client
    monkeypatch.setattr(
        "app.api.pull_requests.create_openai_provider",
        lambda: provider,
    )
    try:
        with TestClient(app) as client:
            return client.post(PATH)
    finally:
        app.dependency_overrides.clear()


def test_openai_review_endpoint_returns_structured_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = FakeProvider()

    response = post_with_provider(monkeypatch, provider)

    assert response.status_code == 200
    assert response.json()["findings"][0]["level"] == "high"
    assert provider.prompt is not None
    assert "<PULL_REQUEST>" in provider.prompt.review_input


@pytest.mark.parametrize(
    ("error", "status", "detail"),
    [
        (AIProviderTimeoutError("sk-secret"), 504, "AI provider request timed out"),
        (AIProviderResponseError("sk-secret"), 502, "AI provider response failed"),
        (AIProviderError("sk-secret"), 502, "AI provider request failed"),
    ],
)
def test_openai_review_endpoint_maps_provider_errors(
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
    status: int,
    detail: str,
) -> None:
    response = post_with_provider(monkeypatch, FakeProvider(error))

    assert response.status_code == status
    assert response.json() == {"detail": detail}
    assert "sk-secret" not in response.text


def test_openai_review_endpoint_maps_missing_configuration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app.dependency_overrides[get_github_client] = github_client
    monkeypatch.setattr(
        "app.api.pull_requests.create_openai_provider",
        lambda: (_ for _ in ()).throw(AIProviderConfigurationError("sk-secret")),
    )
    try:
        with TestClient(app) as client:
            response = client.post(PATH)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"detail": "OpenAI provider is not configured"}
    assert "sk-secret" not in response.text
