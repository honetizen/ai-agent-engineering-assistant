from pydantic import BaseModel

from app.schemas.review import Severity


class ReviewPolicy(BaseModel):
    """Structured project-level requirements for a future AI review."""

    review_focus: list[str]
    custom_instructions: str | None
    severity_rules: dict[str, Severity]
    output_requirements: list[str]
