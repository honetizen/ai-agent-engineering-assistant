import asyncio
from unittest.mock import AsyncMock

from app.services.github_client import GitHubClient, GitHubNotFoundError
from app.services.project_context_service import get_project_context


def test_project_context_reads_readme_and_allows_missing_documents() -> None:
    client = AsyncMock(spec=GitHubClient)
    client.get_repository_file.side_effect = [
        "# Example project",
        GitHubNotFoundError(),
        GitHubNotFoundError(),
    ]

    context = asyncio.run(
        get_project_context("example", "project", github_client=client)
    )

    assert context.readme == "# Example project"
    assert context.architecture is None
    assert context.contributing is None
    assert client.get_repository_file.await_count == 3


def test_project_context_combines_multiple_documents() -> None:
    client = AsyncMock(spec=GitHubClient)
    client.get_repository_file.side_effect = [
        "# Readme",
        "# Architecture",
        "# Contributing",
    ]

    context = asyncio.run(
        get_project_context("example", "project", github_client=client)
    )

    assert context.model_dump() == {
        "readme": "# Readme",
        "architecture": "# Architecture",
        "contributing": "# Contributing",
    }
    assert client.get_repository_file.await_args_list[0].args == (
        "example",
        "project",
        "README.md",
    )
    assert client.get_repository_file.await_args_list[1].args == (
        "example",
        "project",
        "ARCHITECTURE.md",
    )
    assert client.get_repository_file.await_args_list[2].args == (
        "example",
        "project",
        "CONTRIBUTING.md",
    )
