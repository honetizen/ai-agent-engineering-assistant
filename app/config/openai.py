import os

from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError

from app.exceptions.ai_provider import AIProviderConfigurationError


class OpenAIProviderConfig(BaseModel):
    """Validated server-side configuration for the OpenAI provider."""

    model_config = ConfigDict(frozen=True)

    api_key: SecretStr
    model: str = Field(min_length=1)
    timeout_seconds: float = Field(default=60.0, gt=0)
    max_output_tokens: int = Field(default=4_000, gt=0)


def load_openai_provider_config() -> OpenAIProviderConfig:
    """Load OpenAI settings without exposing the API key."""
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key is None or not api_key.strip():
        raise AIProviderConfigurationError(
            "OPENAI_API_KEY is required for the OpenAI provider"
        )

    model = os.getenv("OPENAI_REVIEW_MODEL")
    if model is None or not model.strip():
        raise AIProviderConfigurationError(
            "OPENAI_REVIEW_MODEL is required for the OpenAI review provider"
        )

    try:
        return OpenAIProviderConfig(
            api_key=SecretStr(api_key.strip()),
            model=model.strip(),
            timeout_seconds=os.getenv("OPENAI_TIMEOUT_SECONDS", "60"),
            max_output_tokens=os.getenv(
                "OPENAI_MAX_OUTPUT_TOKENS",
                "4000",
            ),
        )
    except ValidationError as exc:
        raise AIProviderConfigurationError(
            "OpenAI provider environment configuration is invalid"
        ) from exc
