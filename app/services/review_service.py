from app.rules.basic_rules import BASIC_RULES
from app.schemas.diff import PullRequestFile
from app.schemas.review import ReviewFinding, ReviewReport, Severity


def review_pull_request(files: list[PullRequestFile]) -> ReviewReport:
    """Run all deterministic review rules and aggregate their findings."""
    findings = [
        finding
        for rule in BASIC_RULES
        for finding in rule(files)
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
