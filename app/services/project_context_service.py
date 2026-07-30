from app.schemas.project_context import ProjectContext
from app.services.github_client import GitHubClient, GitHubNotFoundError


async def get_project_context(
    owner: str,
    repo: str,
    github_client: GitHubClient | None = None,
) -> ProjectContext:
    """Read selected project documents without scanning the repository."""
    client = github_client if github_client is not None else GitHubClient()

    return ProjectContext(
        readme=await _get_optional_file(client, owner, repo, "README.md"),
        architecture=await _get_optional_file(
            client,
            owner,
            repo,
            "ARCHITECTURE.md",
        ),
        contributing=await _get_optional_file(
            client,
            owner,
            repo,
            "CONTRIBUTING.md",
        ),
    )


async def _get_optional_file(
    github_client: GitHubClient,
    owner: str,
    repo: str,
    path: str,
) -> str | None:
    try:
        return await github_client.get_repository_file(owner, repo, path)
    except GitHubNotFoundError:
        return None
