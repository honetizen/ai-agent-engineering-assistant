from pydantic import BaseModel, Field


class PromptTruncation(BaseModel):
    """Visible metadata describing content omitted from a prompt."""

    section: str
    source: str | None
    original_chars: int
    included_chars: int
    reason: str


class AIReviewPrompt(BaseModel):
    """Stable model input produced from a complete review context."""

    system_prompt: str
    review_input: str
    truncations: list[PromptTruncation] = Field(default_factory=list)
