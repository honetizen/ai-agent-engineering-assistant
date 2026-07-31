import asyncio
from unittest.mock import AsyncMock

from app.schemas.diff import PullRequestFile
from app.services.code_context_service import build_code_context
from app.services.github_client import GitHubClient, GitHubNotFoundError


def changed_file(filename: str) -> PullRequestFile:
    return PullRequestFile(
        filename=filename,
        status="modified",
        additions=1,
        deletions=0,
        changes=1,
        patch="@@ -1 +1 @@",
    )


def test_changed_file_content_is_read() -> None:
    client = AsyncMock(spec=GitHubClient)
    client.get_repository_file.return_value = "# Project"

    context = asyncio.run(
        build_code_context(
            "example",
            "project",
            [changed_file("README.md")],
            github_client=client,
        )
    )

    assert context.changed_file_contents == {"README.md": "# Project"}
    assert context.related_test_contents == {}


def test_related_test_file_is_matched() -> None:
    content_by_path = {
        "app/login.py": "def login(): ...",
        "tests/test_login.py": "def test_login(): ...",
    }

    async def get_file(owner: str, repo: str, path: str) -> str:
        try:
            return content_by_path[path]
        except KeyError:
            raise GitHubNotFoundError from None

    client = AsyncMock(spec=GitHubClient)
    client.get_repository_file.side_effect = get_file

    context = asyncio.run(
        build_code_context(
            "example",
            "project",
            [changed_file("app/login.py")],
            github_client=client,
        )
    )

    assert context.changed_file_contents == {
        "app/login.py": "def login(): ..."
    }
    assert context.related_test_contents == {
        "tests/test_login.py": "def test_login(): ..."
    }


def test_no_related_test_file_returns_empty_mapping() -> None:
    async def get_file(owner: str, repo: str, path: str) -> str:
        if path == "app/login.py":
            return "def login(): ..."
        raise GitHubNotFoundError

    client = AsyncMock(spec=GitHubClient)
    client.get_repository_file.side_effect = get_file

    context = asyncio.run(
        build_code_context(
            "example",
            "project",
            [changed_file("app/login.py")],
            github_client=client,
        )
    )

    assert context.changed_file_contents == {
        "app/login.py": "def login(): ..."
    }
    assert context.related_test_contents == {}


def test_missing_changed_file_is_ignored() -> None:
    client = AsyncMock(spec=GitHubClient)
    client.get_repository_file.side_effect = GitHubNotFoundError

    context = asyncio.run(
        build_code_context(
            "example",
            "project",
            [changed_file("app/missing.py")],
            github_client=client,
        )
    )

    assert context.changed_file_contents == {}
    assert context.related_test_contents == {}
