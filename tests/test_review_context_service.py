import asyncio
from unittest.mock import AsyncMock

from app.config.review_config import ReviewRuleConfig
from app.schemas.diff import PullRequestFile
from app.schemas.pull_request import PullRequestMetadata
from app.services.github_client import GitHubClient, GitHubNotFoundError
from app.services.review_context_service import build_review_context


def pull_request_metadata(*, changed_files: int = 1) -> PullRequestMetadata:
    return PullRequestMetadata(
        number=1,
        title="Add review context",
        state="open",
        merged=False,
        author="honetizen",
        base_branch="main",
        head_branch="feature/review-context",
        commits=1,
        changed_files=changed_files,
        additions=5,
        deletions=1,
        html_url="https://github.com/example/project/pull/1",
    )


def changed_file(filename: str) -> PullRequestFile:
    return PullRequestFile(
        filename=filename,
        status="modified",
        additions=4,
        deletions=1,
        changes=5,
        patch="@@ -1 +1,4 @@",
    )


def test_build_review_context_combines_all_inputs() -> None:
    metadata = pull_request_metadata()
    files = [changed_file("app/service.py")]
    client = AsyncMock(spec=GitHubClient)
    client.get_pull_request.return_value = metadata
    client.get_pull_request_files.return_value = files
    client.get_repository_file.side_effect = GitHubNotFoundError

    context = asyncio.run(
        build_review_context(
            "example",
            "project",
            1,
            github_client=client,
        )
    )

    assert context.pull_request == metadata
    assert context.changed_files == files
    assert context.rule_report.files_reviewed == 1
    assert context.rule_report.risk_level == "medium"
    assert context.rule_report.findings[0].rule_id == "missing_tests"
    assert context.project_context.readme is None
    client.get_pull_request.assert_awaited_once_with("example", "project", 1)
    client.get_pull_request_files.assert_awaited_once_with(
        "example",
        "project",
        1,
    )


def test_custom_review_config_affects_rule_report() -> None:
    client = AsyncMock(spec=GitHubClient)
    client.get_pull_request.return_value = pull_request_metadata(
        changed_files=2
    )
    client.get_pull_request_files.return_value = [
        changed_file("src/service.ts"),
        changed_file("spec/service.test.ts"),
    ]
    client.get_repository_file.side_effect = GitHubNotFoundError
    config = ReviewRuleConfig(
        business_extensions=[".ts"],
        test_directories=["spec/"],
    )

    context = asyncio.run(
        build_review_context(
            "example",
            "project",
            1,
            github_client=client,
            review_config=config,
        )
    )

    assert context.rule_report.risk_level == "low"
    assert context.rule_report.findings == []


def test_empty_file_list_builds_context() -> None:
    metadata = pull_request_metadata(changed_files=0)
    client = AsyncMock(spec=GitHubClient)
    client.get_pull_request.return_value = metadata
    client.get_pull_request_files.return_value = []
    client.get_repository_file.side_effect = GitHubNotFoundError

    context = asyncio.run(
        build_review_context(
            "example",
            "project",
            1,
            github_client=client,
        )
    )

    assert context.pull_request == metadata
    assert context.changed_files == []
    assert context.rule_report.files_reviewed == 0
    assert context.rule_report.findings == []
    assert context.rule_report.risk_level == "low"
    assert context.project_context.model_dump() == {
        "readme": None,
        "architecture": None,
        "contributing": None,
    }
