import pytest
from pydantic import ValidationError

from app.config.review_config import DEFAULT_REVIEW_CONFIG, ReviewRuleConfig
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
    findings = missing_tests(
        [changed_file("app/service.py")],
        DEFAULT_REVIEW_CONFIG,
    )

    assert len(findings) == 1
    assert findings[0].rule_id == "missing_tests"
    assert findings[0].severity == "medium"
    assert findings[0].filename is None


def test_missing_tests_not_returned_when_python_tests_change() -> None:
    files = [
        changed_file("app/service.py"),
        changed_file("tests/test_service.py"),
    ]

    assert missing_tests(files, DEFAULT_REVIEW_CONFIG) == []


def test_sensitive_file_change_returns_high_finding() -> None:
    findings = sensitive_file_changed(
        [changed_file("app/settings/database.py")],
        DEFAULT_REVIEW_CONFIG,
    )

    assert len(findings) == 1
    assert findings[0].rule_id == "sensitive_file_changed"
    assert findings[0].severity == "high"
    assert findings[0].filename == "app/settings/database.py"


def test_large_pull_request_when_total_changes_exceed_limit() -> None:
    findings = large_pull_request(
        [changed_file("README.md", changes=301)],
        DEFAULT_REVIEW_CONFIG,
    )

    assert len(findings) == 1
    assert findings[0].rule_id == "large_pull_request"
    assert findings[0].severity == "medium"


def test_large_pull_request_when_file_count_exceeds_limit() -> None:
    files = [changed_file(f"docs/page-{index}.md") for index in range(11)]

    findings = large_pull_request(files, DEFAULT_REVIEW_CONFIG)

    assert len(findings) == 1
    assert findings[0].rule_id == "large_pull_request"


def test_patch_unavailable_returns_finding_for_file() -> None:
    findings = patch_unavailable(
        [changed_file("assets/logo.png", patch=None)],
        DEFAULT_REVIEW_CONFIG,
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


def test_custom_test_directory_is_recognized() -> None:
    config = ReviewRuleConfig(test_directories=["QA/"])
    files = [
        changed_file("src/service.py"),
        changed_file("qa/test_service.py"),
    ]

    assert missing_tests(files, config) == []


def test_custom_business_extension_is_reviewed() -> None:
    config = ReviewRuleConfig(
        business_extensions=[".TS"],
        test_directories=["spec/"],
    )

    findings = missing_tests([changed_file("src/service.ts")], config)

    assert len(findings) == 1
    assert findings[0].rule_id == "missing_tests"


def test_custom_sensitive_patterns_replace_defaults() -> None:
    config = ReviewRuleConfig(sensitive_patterns=["private"])
    files = [
        changed_file("app/config.py"),
        changed_file("docs/PRIVATE-notes.md"),
    ]

    findings = sensitive_file_changed(files, config)

    assert [finding.filename for finding in findings] == [
        "docs/PRIVATE-notes.md"
    ]


def test_custom_large_pull_request_thresholds_are_used() -> None:
    config = ReviewRuleConfig(max_files=2, max_changes=5)

    by_file_count = large_pull_request(
        [changed_file(f"file-{index}.md") for index in range(3)],
        config,
    )
    by_changes = large_pull_request(
        [changed_file("README.md", changes=6)],
        config,
    )

    assert len(by_file_count) == 1
    assert len(by_changes) == 1


def test_review_service_uses_default_config_when_omitted() -> None:
    report = review_pull_request([changed_file("app/service.py")])

    assert any(
        finding.rule_id == "missing_tests"
        for finding in report.findings
    )


def test_review_service_accepts_custom_config() -> None:
    config = ReviewRuleConfig(
        business_extensions=[".ts"],
        test_directories=["spec/"],
        sensitive_patterns=["restricted"],
        max_files=20,
        max_changes=500,
    )
    files = [
        changed_file("src/service.ts"),
        changed_file("spec/service.test.ts"),
    ]

    report = review_pull_request(files, config)

    assert report.risk_level == "low"
    assert report.findings == []


def test_review_config_requires_positive_thresholds() -> None:
    with pytest.raises(ValidationError):
        ReviewRuleConfig(max_files=0)
    with pytest.raises(ValidationError):
        ReviewRuleConfig(max_changes=-1)
