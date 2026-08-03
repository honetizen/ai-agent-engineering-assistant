import pytest

from app.config.openai import load_openai_provider_config
from app.exceptions.ai_provider import AIProviderConfigurationError


def test_load_openai_provider_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-private-test")
    monkeypatch.setenv("OPENAI_REVIEW_MODEL", "test-model")
    monkeypatch.setenv("OPENAI_TIMEOUT_SECONDS", "12.5")
    monkeypatch.setenv("OPENAI_MAX_OUTPUT_TOKENS", "900")

    config = load_openai_provider_config()

    assert config.api_key.get_secret_value() == "sk-private-test"
    assert config.model == "test-model"
    assert config.timeout_seconds == 12.5
    assert config.max_output_tokens == 900
    assert "sk-private-test" not in repr(config)


def test_missing_openai_api_key_is_configuration_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(AIProviderConfigurationError):
        load_openai_provider_config()


def test_missing_openai_review_model_is_configuration_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-private-test")
    monkeypatch.delenv("OPENAI_REVIEW_MODEL", raising=False)

    with pytest.raises(
        AIProviderConfigurationError,
        match="OPENAI_REVIEW_MODEL is required for the OpenAI review provider",
    ) as error:
        load_openai_provider_config()

    assert "sk-private-test" not in str(error.value)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("OPENAI_TIMEOUT_SECONDS", "0"),
        ("OPENAI_TIMEOUT_SECONDS", "invalid"),
        ("OPENAI_MAX_OUTPUT_TOKENS", "-1"),
        ("OPENAI_MAX_OUTPUT_TOKENS", "invalid"),
    ],
)
def test_invalid_numeric_configuration_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    value: str,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-private-test")
    monkeypatch.setenv("OPENAI_REVIEW_MODEL", "test-model")
    monkeypatch.setenv(name, value)

    with pytest.raises(AIProviderConfigurationError):
        load_openai_provider_config()
