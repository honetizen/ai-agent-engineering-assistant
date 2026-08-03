import asyncio
from typing import Any

from openai import APITimeoutError, AsyncOpenAI, OpenAIError
from pydantic import ValidationError

from app.config.openai import (
    OpenAIProviderConfig,
    load_openai_provider_config,
)
from app.exceptions.ai_provider import (
    AIProviderError,
    AIProviderResponseError,
    AIProviderTimeoutError,
)
from app.schemas.ai_prompt import AIReviewPrompt
from app.schemas.ai_review import AIReviewReport
from app.services.ai_provider import AIProvider


class OpenAIProvider(AIProvider):
    """Asynchronous Responses API provider with strict structured output."""

    def __init__(
        self,
        config: OpenAIProviderConfig,
        client: Any | None = None,
    ) -> None:
        self._config = config
        self._client = client or AsyncOpenAI(
            api_key=config.api_key.get_secret_value(),
            timeout=config.timeout_seconds,
        )

    async def review(self, prompt: AIReviewPrompt) -> AIReviewReport:
        try:
            response = await self._client.responses.create(
                model=self._config.model,
                input=[
                    {"role": "system", "content": prompt.system_prompt},
                    {"role": "user", "content": prompt.review_input},
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "ai_review_report",
                        "strict": True,
                        "schema": AIReviewReport.model_json_schema(),
                    }
                },
                max_output_tokens=self._config.max_output_tokens,
                store=False,
                timeout=self._config.timeout_seconds,
            )
        except (APITimeoutError, asyncio.TimeoutError) as exc:
            raise AIProviderTimeoutError(
                "OpenAI review request timed out"
            ) from exc
        except OpenAIError as exc:
            raise AIProviderError("OpenAI review request failed") from exc

        if getattr(response, "status", None) != "completed":
            raise AIProviderResponseError(
                "OpenAI response did not complete successfully"
            )

        output_text_parts: list[str] = []
        for output in getattr(response, "output", []):
            if getattr(output, "type", None) != "message":
                continue
            for item in getattr(output, "content", []):
                item_type = getattr(item, "type", None)
                if item_type == "refusal":
                    raise AIProviderResponseError(
                        "OpenAI refused the review request"
                    )
                if item_type == "output_text":
                    text = getattr(item, "text", None)
                    if isinstance(text, str):
                        output_text_parts.append(text)

        output_text = "".join(output_text_parts).strip()
        if not output_text:
            raise AIProviderResponseError(
                "OpenAI returned no structured review output"
            )

        try:
            return AIReviewReport.model_validate_json(output_text)
        except (ValidationError, ValueError) as exc:
            raise AIProviderResponseError(
                "OpenAI returned an invalid structured review report"
            ) from exc


def create_openai_provider(
    config: OpenAIProviderConfig | None = None,
) -> OpenAIProvider:
    """Explicitly construct the paid provider from server configuration."""
    active_config = config or load_openai_provider_config()
    return OpenAIProvider(active_config)
