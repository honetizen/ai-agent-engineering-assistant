from typing import Literal

from pydantic import BaseModel


class AIReviewFinding(BaseModel):
    """A structured issue returned by an AI review provider."""

    level: Literal["low", "medium", "high"]
    file: str
    line: int | None
    issue: str
    suggestion: str


class AIReviewReport(BaseModel):
    """Structured output of the replaceable AI review layer."""

    summary: str
    findings: list[AIReviewFinding]
