from app.schemas.ai_review import AIReviewReport
from app.schemas.review_context import ReviewContext
from app.services.ai_provider import AIProvider


class MockAIProvider(AIProvider):
    """Deterministic provider used before a real AI integration exists."""

    def review(self, context: ReviewContext) -> AIReviewReport:
        return AIReviewReport(
            summary="Mock AI review completed",
            findings=[],
        )
