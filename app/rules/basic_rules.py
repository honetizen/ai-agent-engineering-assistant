from collections.abc import Callable

from app.config.review_config import ReviewRuleConfig
from app.schemas.diff import PullRequestFile
from app.schemas.review import ReviewFinding


def _normalized_path(filename: str) -> str:
    return filename.replace("\\", "/").lower()


def _has_business_extension(
    filename: str,
    config: ReviewRuleConfig,
) -> bool:
    normalized = _normalized_path(filename)
    return any(
        normalized.endswith(extension)
        for extension in config.business_extensions
    )


def _is_in_test_directory(
    filename: str,
    config: ReviewRuleConfig,
) -> bool:
    normalized = _normalized_path(filename)
    return any(
        normalized.startswith(directory)
        for directory in config.test_directories
    )


def missing_tests(
    files: list[PullRequestFile],
    config: ReviewRuleConfig,
) -> list[ReviewFinding]:
    """Flag business-file changes when no configured test file changed."""
    has_business_file = any(
        _has_business_extension(file.filename, config)
        and not _is_in_test_directory(file.filename, config)
        for file in files
    )
    has_test_file = any(
        _has_business_extension(file.filename, config)
        and _is_in_test_directory(file.filename, config)
        for file in files
    )

    if has_business_file and not has_test_file:
        return [
            ReviewFinding(
                rule_id="missing_tests",
                severity="medium",
                message="Python business files changed without Python test changes.",
            )
        ]
    return []


def sensitive_file_changed(
    files: list[PullRequestFile],
    config: ReviewRuleConfig,
) -> list[ReviewFinding]:
    """Flag every changed file whose path contains a sensitive keyword."""
    findings = []
    for file in files:
        normalized = _normalized_path(file.filename)
        if any(pattern in normalized for pattern in config.sensitive_patterns):
            findings.append(
                ReviewFinding(
                    rule_id="sensitive_file_changed",
                    severity="high",
                    message="A potentially sensitive file was changed.",
                    filename=file.filename,
                )
            )
    return findings


def large_pull_request(
    files: list[PullRequestFile],
    config: ReviewRuleConfig,
) -> list[ReviewFinding]:
    """Flag pull requests that exceed file-count or total-change limits."""
    total_changes = sum(file.changes for file in files)
    if len(files) > config.max_files or total_changes > config.max_changes:
        return [
            ReviewFinding(
                rule_id="large_pull_request",
                severity="medium",
                message="Pull request exceeds the review size threshold.",
            )
        ]
    return []


def patch_unavailable(
    files: list[PullRequestFile],
    config: ReviewRuleConfig,
) -> list[ReviewFinding]:
    """Flag every file for which GitHub did not provide patch content."""
    return [
        ReviewFinding(
            rule_id="patch_unavailable",
            severity="low",
            message="Patch content is unavailable for this file.",
            filename=file.filename,
        )
        for file in files
        if file.patch is None
    ]


Rule = Callable[
    [list[PullRequestFile], ReviewRuleConfig],
    list[ReviewFinding],
]

BASIC_RULES: tuple[Rule, ...] = (
    missing_tests,
    sensitive_file_changed,
    large_pull_request,
    patch_unavailable,
)
