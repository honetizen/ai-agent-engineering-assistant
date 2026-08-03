from app.schemas.ai_review import AIReviewReport
from app.schemas.review_context import ReviewContext
from app.services.ai_provider import AIProvider
from app.services.mock_ai_provider import MockAIProvider


def review_context(
    context: ReviewContext,
    provider: AIProvider | None = None,
) -> AIReviewReport:
    """Delegate an already-built review context to an AI provider."""
    active_provider = provider if provider is not None else MockAIProvider()
    return active_provider.review(context)
