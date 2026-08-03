class AIProviderError(Exception):
    """Base error for safe failures in the AI provider layer."""


class AIProviderConfigurationError(AIProviderError):
    """Raised when a provider cannot be configured safely."""


class AIProviderTimeoutError(AIProviderError):
    """Raised when an AI provider request times out."""


class AIProviderResponseError(AIProviderError):
    """Raised when a provider returns no valid structured report."""
