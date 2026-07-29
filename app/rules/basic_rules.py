from collections.abc import Callable

from app.schemas.diff import PullRequestFile
from app.schemas.review import ReviewFinding


SENSITIVE_FILE_KEYWORDS = (
    ".env",
    "secret",
    "credential",
    "token",
    "key",
    "settings",
    "config",
)


def _normalized_path(filename: str) -> str:
    return filename.replace("\\", "/").lower()


def _is_test_python_file(filename: str) -> bool:
    normalized = _normalized_path(filename)
    return normalized.startswith("tests/") and normalized.endswith(".py")


def missing_tests(files: list[PullRequestFile]) -> list[ReviewFinding]:
    """Flag Python business changes when no Python test file changed."""
    has_business_python = any(
        _normalized_path(file.filename).endswith(".py")
        and not _normalized_path(file.filename).startswith("tests/")
        for file in files
    )
    has_python_tests = any(_is_test_python_file(file.filename) for file in files)

    if has_business_python and not has_python_tests:
        return [
            ReviewFinding(
                rule_id="missing_tests",
                severity="medium",
                message="Python business files changed without Python test changes.",
            )
        ]
    return []


def sensitive_file_changed(files: list[PullRequestFile]) -> list[ReviewFinding]:
    """Flag every changed file whose path contains a sensitive keyword."""
    findings = []
    for file in files:
        normalized = _normalized_path(file.filename)
        if any(keyword in normalized for keyword in SENSITIVE_FILE_KEYWORDS):
            findings.append(
                ReviewFinding(
                    rule_id="sensitive_file_changed",
                    severity="high",
                    message="A potentially sensitive file was changed.",
                    filename=file.filename,
                )
            )
    return findings


def large_pull_request(files: list[PullRequestFile]) -> list[ReviewFinding]:
    """Flag pull requests that exceed file-count or total-change limits."""
    total_changes = sum(file.changes for file in files)
    if len(files) > 10 or total_changes > 300:
        return [
            ReviewFinding(
                rule_id="large_pull_request",
                severity="medium",
                message="Pull request exceeds the review size threshold.",
            )
        ]
    return []


def patch_unavailable(files: list[PullRequestFile]) -> list[ReviewFinding]:
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


Rule = Callable[[list[PullRequestFile]], list[ReviewFinding]]

BASIC_RULES: tuple[Rule, ...] = (
    missing_tests,
    sensitive_file_changed,
    large_pull_request,
    patch_unavailable,
)
