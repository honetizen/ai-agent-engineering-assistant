import asyncio
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.config.review_policy import DEFAULT_REVIEW_POLICY
from app.schemas.pull_request import PullRequestMetadata
from app.schemas.review_policy import ReviewPolicy
from app.services.github_client import GitHubClient, GitHubNotFoundError
from app.services.review_context_service import build_review_context


def test_default_review_policy_is_loaded() -> None:
    assert DEFAULT_REVIEW_POLICY.review_focus == [
        "correctness",
        "security",
        "architecture",
        "test",
    ]
    assert DEFAULT_REVIEW_POLICY.custom_instructions is None
    assert DEFAULT_REVIEW_POLICY.severity_rules == {
        "security": "high",
        "architecture": "medium",
    }
    assert DEFAULT_REVIEW_POLICY.output_requirements == [
        "必须指出文件位置",
        "必须提供修改建议",
    ]


def test_custom_review_policy() -> None:
    policy = ReviewPolicy(
        review_focus=["performance"],
        custom_instructions="重点检查数据库查询次数",
        severity_rules={"performance": "medium"},
        output_requirements=["必须说明性能影响"],
    )

    assert policy.review_focus == ["performance"]
    assert policy.custom_instructions == "重点检查数据库查询次数"
    assert policy.severity_rules == {"performance": "medium"}
    assert policy.output_requirements == ["必须说明性能影响"]


def test_review_policy_rejects_unknown_severity() -> None:
    with pytest.raises(ValidationError):
        ReviewPolicy(
            review_focus=["security"],
            custom_instructions=None,
            severity_rules={"security": "critical"},
            output_requirements=[],
        )


def test_review_context_contains_review_policy() -> None:
    metadata = PullRequestMetadata(
        number=1,
        title="Add review policy",
        state="open",
        merged=False,
        author="developer",
        base_branch="main",
        head_branch="feature/review-policy",
        base_sha="base-sha-123",
        head_sha="head-sha-456",
        base_repository="example/project",
        head_repository="example/project",
        commits=1,
        changed_files=0,
        additions=0,
        deletions=0,
        html_url="https://github.com/example/project/pull/1",
    )
    custom_policy = ReviewPolicy(
        review_focus=["maintainability"],
        custom_instructions=None,
        severity_rules={"maintainability": "low"},
        output_requirements=["必须给出文件位置"],
    )
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
            review_policy=custom_policy,
        )
    )

    assert context.review_policy is custom_policy
