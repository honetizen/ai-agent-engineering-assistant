from typing import Literal

from pydantic import BaseModel, ConfigDict


class AIReviewFinding(BaseModel):
    """A structured issue returned by an AI review provider."""

    model_config = ConfigDict(extra="forbid")

    level: Literal["low", "medium", "high"]
    file: str
    line: int | None
    issue: str
    suggestion: str


class AIReviewReport(BaseModel):
    """Structured output of the replaceable AI review layer."""

    model_config = ConfigDict(extra="forbid")

    summary: str
    findings: list[AIReviewFinding]
