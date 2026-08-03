from pydantic import BaseModel


class AIReviewPrompt(BaseModel):
    """Stable model input produced from a complete review context."""

    system_prompt: str
    review_input: str
