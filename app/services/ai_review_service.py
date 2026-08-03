from app.schemas.ai_review import AIReviewReport
from app.schemas.review_context import ReviewContext
from app.services.ai_provider import AIProvider
from app.services.mock_ai_provider import MockAIProvider
from app.services.prompt_builder import build_ai_review_prompt


async def review_context(
    context: ReviewContext,
    provider: AIProvider | None = None,
) -> AIReviewReport:
    """Build stable model input and delegate it to an AI provider."""
    active_provider = provider if provider is not None else MockAIProvider()
    prompt = build_ai_review_prompt(context)
    return await active_provider.review(prompt)
