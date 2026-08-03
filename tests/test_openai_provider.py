import asyncio
import json
from types import SimpleNamespace
from typing import Any

import pytest
from openai import OpenAIError
from pydantic import SecretStr

from app.config.openai import OpenAIProviderConfig
from app.exceptions.ai_provider import (
    AIProviderError,
    AIProviderResponseError,
    AIProviderTimeoutError,
)
from app.schemas.ai_prompt import AIReviewPrompt
from app.schemas.ai_review import AIReviewReport
from app.services.openai_provider import OpenAIProvider


class FakeResponses:
    def __init__(self, response: Any = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.kwargs: dict[str, Any] | None = None

    async def create(self, **kwargs: Any) -> Any:
        self.kwargs = kwargs
        if self.error is not None:
            raise self.error
        return self.response


class FakeClient:
    def __init__(self, responses: FakeResponses) -> None:
        self.responses = responses


def config() -> OpenAIProviderConfig:
    return OpenAIProviderConfig(
        api_key=SecretStr("sk-private-test"),
        model="test-model",
        timeout_seconds=12.5,
        max_output_tokens=900,
    )


def prompt() -> AIReviewPrompt:
    return AIReviewPrompt(system_prompt="system rules", review_input="review data")


def completed_response(content: list[Any]) -> Any:
    return SimpleNamespace(
        status="completed",
        output=[SimpleNamespace(type="message", content=content)],
    )


def output_text(payload: object) -> Any:
    return SimpleNamespace(type="output_text", text=json.dumps(payload))


def test_provider_uses_responses_api_and_strict_schema() -> None:
    payload = {
        "summary": "Review completed",
        "findings": [
            {"level": level, "file": f"{level}.py", "line": None,
             "issue": "issue", "suggestion": "suggestion"}
            for level in ("low", "medium", "high")
        ],
    }
    responses = FakeResponses(completed_response([output_text(payload)]))
    provider = OpenAIProvider(config(), client=FakeClient(responses))

    report = asyncio.run(provider.review(prompt()))

    assert isinstance(report, AIReviewReport)
    assert [finding.level for finding in report.findings] == ["low", "medium", "high"]
    assert responses.kwargs is not None
    assert responses.kwargs["model"] == "test-model"
    assert responses.kwargs["input"] == [
        {"role": "system", "content": "system rules"},
        {"role": "user", "content": "review data"},
    ]
    assert responses.kwargs["store"] is False
    assert responses.kwargs["max_output_tokens"] == 900
    assert responses.kwargs["timeout"] == 12.5
    format_config = responses.kwargs["text"]["format"]
    assert format_config["type"] == "json_schema"
    assert format_config["strict"] is True
    assert format_config["schema"] == AIReviewReport.model_json_schema()
    assert format_config["schema"]["additionalProperties"] is False


@pytest.mark.parametrize(
    "response",
    [
        completed_response([]),
        completed_response([SimpleNamespace(type="output_text", text="")]),
        completed_response([output_text({"summary": "x", "findings": [
            {"level": "critical", "file": "x.py", "line": None,
             "issue": "x", "suggestion": "x"}
        ]})]),
        completed_response([SimpleNamespace(type="output_text", text="not-json")]),
        SimpleNamespace(status="incomplete", output=[]),
    ],
)
def test_invalid_or_incomplete_output_is_rejected(response: Any) -> None:
    provider = OpenAIProvider(config(), client=FakeClient(FakeResponses(response)))

    with pytest.raises(AIProviderResponseError):
        asyncio.run(provider.review(prompt()))


def test_refusal_is_rejected() -> None:
    response = completed_response([
        SimpleNamespace(type="refusal", refusal="Cannot comply")
    ])
    provider = OpenAIProvider(config(), client=FakeClient(FakeResponses(response)))

    with pytest.raises(AIProviderResponseError, match="refused"):
        asyncio.run(provider.review(prompt()))


def test_timeout_is_mapped_without_leaking_key() -> None:
    provider = OpenAIProvider(
        config(),
        client=FakeClient(FakeResponses(error=asyncio.TimeoutError("sk-private-test"))),
    )

    with pytest.raises(AIProviderTimeoutError) as error:
        asyncio.run(provider.review(prompt()))
    assert "sk-private-test" not in str(error.value)


def test_sdk_error_is_mapped_without_leaking_key() -> None:
    provider = OpenAIProvider(
        config(),
        client=FakeClient(FakeResponses(error=OpenAIError("sk-private-test"))),
    )

    with pytest.raises(AIProviderError) as error:
        asyncio.run(provider.review(prompt()))
    assert "sk-private-test" not in str(error.value)
