from typing import Protocol

from app.schemas.ai_prompt import AIReviewPrompt
from app.schemas.ai_review import AIReviewReport


class AIProvider(Protocol):
    """Model-agnostic capability required by the AI review service."""

    def review(self, prompt: AIReviewPrompt) -> AIReviewReport:
        """Review prepared model input and return a structured report."""
        ...
