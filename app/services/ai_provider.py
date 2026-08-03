from typing import Protocol

from app.schemas.ai_review import AIReviewReport
from app.schemas.review_context import ReviewContext


class AIProvider(Protocol):
    """Model-agnostic capability required by the AI review service."""

    def review(self, context: ReviewContext) -> AIReviewReport:
        """Review a prepared context and return a structured report."""
        ...
