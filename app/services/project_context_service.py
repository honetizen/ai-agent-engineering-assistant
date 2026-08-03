from app.schemas.project_context import ProjectContext
from app.services.github_client import GitHubClient, GitHubNotFoundError
from app.services.repository import split_repository_full_name


async def get_project_context(
    repository: str,
    ref: str,
    github_client: GitHubClient | None = None,
) -> ProjectContext:
    """Read selected baseline documents from an immutable repository ref."""
    owner, repo = split_repository_full_name(repository)
    client = github_client if github_client is not None else GitHubClient()

    return ProjectContext(
        readme=await _get_optional_file(
            client,
            owner,
            repo,
            "README.md",
            ref,
        ),
        architecture=await _get_optional_file(
            client,
            owner,
            repo,
            "ARCHITECTURE.md",
            ref,
        ),
        contributing=await _get_optional_file(
            client,
            owner,
            repo,
            "CONTRIBUTING.md",
            ref,
        ),
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
