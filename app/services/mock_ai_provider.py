from app.schemas.ai_prompt import AIReviewPrompt
from app.schemas.ai_review import AIReviewReport
from app.services.ai_provider import AIProvider


class MockAIProvider(AIProvider):
    """Deterministic provider used before a real AI integration exists."""

    async def review(self, prompt: AIReviewPrompt) -> AIReviewReport:
        return AIReviewReport(
            summary="Mock AI review completed",
            findings=[],
        )
