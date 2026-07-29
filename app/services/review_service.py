from app.config.review_config import DEFAULT_REVIEW_CONFIG, ReviewRuleConfig
from app.rules.basic_rules import BASIC_RULES
from app.schemas.diff import PullRequestFile
from app.schemas.review import ReviewFinding, ReviewReport, Severity


def review_pull_request(
    files: list[PullRequestFile],
    config: ReviewRuleConfig | None = None,
) -> ReviewReport:
    """Run all deterministic review rules and aggregate their findings."""
    active_config = config or DEFAULT_REVIEW_CONFIG
    findings = [
        finding
        for rule in BASIC_RULES
        for finding in rule(files, active_config)
    ]
    risk_level = _calculate_risk_level(findings)
    return ReviewReport(
        risk_level=risk_level,
        findings=findings,
        files_reviewed=len(files),
    )


def _calculate_risk_level(findings: list[ReviewFinding]) -> Severity:
    severities = {finding.severity for finding in findings}
    if "high" in severities:
        return "high"
    if "medium" in severities:
        return "medium"
    return "low"
