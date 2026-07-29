from typing import Literal

from pydantic import BaseModel


Severity = Literal["low", "medium", "high"]


class ReviewFinding(BaseModel):
    """A deterministic issue identified while reviewing a pull request."""

    rule_id: str
    severity: Severity
    message: str
    filename: str | None = None


class ReviewReport(BaseModel):
    """Aggregated result of deterministic pull request review rules."""

    risk_level: Severity
    findings: list[ReviewFinding]
    files_reviewed: int
