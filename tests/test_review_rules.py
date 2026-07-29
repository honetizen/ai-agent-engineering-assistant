from app.rules.basic_rules import (
    large_pull_request,
    missing_tests,
    patch_unavailable,
    sensitive_file_changed,
)
from app.schemas.diff import PullRequestFile
from app.services.review_service import review_pull_request


def changed_file(
    filename: str,
    *,
    changes: int = 1,
    patch: str | None = "@@ -1 +1 @@",
) -> PullRequestFile:
    return PullRequestFile(
        filename=filename,
        status="modified",
        additions=changes,
        deletions=0,
        changes=changes,
        patch=patch,
    )


def test_missing_tests_when_business_python_changes_without_tests() -> None:
    findings = missing_tests([changed_file("app/service.py")])

    assert len(findings) == 1
    assert findings[0].rule_id == "missing_tests"
    assert findings[0].severity == "medium"
    assert findings[0].filename is None


def test_missing_tests_not_returned_when_python_tests_change() -> None:
    files = [
        changed_file("app/service.py"),
        changed_file("tests/test_service.py"),
    ]

    assert missing_tests(files) == []


def test_sensitive_file_change_returns_high_finding() -> None:
    findings = sensitive_file_changed(
        [changed_file("app/settings/database.py")]
    )

    assert len(findings) == 1
    assert findings[0].rule_id == "sensitive_file_changed"
    assert findings[0].severity == "high"
    assert findings[0].filename == "app/settings/database.py"


def test_large_pull_request_when_total_changes_exceed_limit() -> None:
    findings = large_pull_request([changed_file("README.md", changes=301)])

    assert len(findings) == 1
    assert findings[0].rule_id == "large_pull_request"
    assert findings[0].severity == "medium"


def test_large_pull_request_when_file_count_exceeds_limit() -> None:
    files = [changed_file(f"docs/page-{index}.md") for index in range(11)]

    findings = large_pull_request(files)

    assert len(findings) == 1
    assert findings[0].rule_id == "large_pull_request"


def test_patch_unavailable_returns_finding_for_file() -> None:
    findings = patch_unavailable(
        [changed_file("assets/logo.png", patch=None)]
    )

    assert len(findings) == 1
    assert findings[0].rule_id == "patch_unavailable"
    assert findings[0].severity == "low"
    assert findings[0].filename == "assets/logo.png"


def test_review_report_aggregates_highest_risk_level() -> None:
    report = review_pull_request(
        [
            changed_file("app/service.py"),
            changed_file(".env.example"),
            changed_file("assets/logo.png", patch=None),
        ]
    )

    assert report.risk_level == "high"
    assert report.files_reviewed == 3
    assert {finding.severity for finding in report.findings} == {
        "low",
        "medium",
        "high",
    }

    medium_report = review_pull_request([changed_file("app/service.py")])
    low_report = review_pull_request([changed_file("README.md")])

    assert medium_report.risk_level == "medium"
    assert low_report.risk_level == "low"
