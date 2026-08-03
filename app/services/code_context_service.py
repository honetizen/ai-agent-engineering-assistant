from pathlib import PurePosixPath

from app.schemas.code_context import CodeContext
from app.schemas.diff import PullRequestFile
from app.services.github_client import GitHubClient, GitHubNotFoundError
from app.services.repository import split_repository_full_name


async def build_code_context(
    repository: str,
    ref: str,
    changed_files: list[PullRequestFile],
    github_client: GitHubClient | None = None,
) -> CodeContext:
    """Fetch changed files and fixed-path test candidates without scanning."""
    owner, repo = split_repository_full_name(repository)
    client = github_client if github_client is not None else GitHubClient()
    changed_file_contents: dict[str, str] = {}
    related_test_contents: dict[str, str] = {}

    for file in changed_files:
        content = await _get_optional_file(
            client,
            owner,
            repo,
            file.filename,
            ref,
        )
        if content is not None:
            changed_file_contents[file.filename] = content

    test_candidates = {
        candidate
        for file in changed_files
        for candidate in _related_test_candidates(file.filename)
    }
    for test_path in sorted(test_candidates):
        content = await _get_optional_file(
            client,
            owner,
            repo,
            test_path,
            ref,
        )
        if content is not None:
            related_test_contents[test_path] = content

    return CodeContext(
        changed_file_contents=changed_file_contents,
        related_test_contents=related_test_contents,
    )


def _related_test_candidates(filename: str) -> tuple[str, ...]:
    normalized = filename.replace("\\", "/").lower()
    if normalized.startswith("tests/") or not normalized.endswith(".py"):
        return ()

    stem = PurePosixPath(normalized).stem
    return (
        f"tests/test_{stem}.py",
        f"tests/{stem}_test.py",
    )


async def _get_optional_file(
    github_client: GitHubClient,
    owner: str,
    repo: str,
    path: str,
    ref: str,
) -> str | None:
    try:
        return await github_client.get_repository_file(
            owner,
            repo,
            path,
            ref=ref,
        )
    except GitHubNotFoundError:
        return None
