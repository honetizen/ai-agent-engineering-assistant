from app.config.review_config import ReviewRuleConfig
from app.schemas.review_context import ReviewContext
from app.services.github_client import GitHubClient
from app.services.review_service import review_pull_request


async def build_review_context(
    owner: str,
    repo: str,
    pull_number: int,
    github_client: GitHubClient | None = None,
    review_config: ReviewRuleConfig | None = None,
) -> ReviewContext:
    """Fetch PR inputs, run deterministic rules, and combine the results."""
    client = github_client if github_client is not None else GitHubClient()
    pull_request = await client.get_pull_request(owner, repo, pull_number)
    changed_files = await client.get_pull_request_files(
        owner,
        repo,
        pull_number,
    )
    rule_report = review_pull_request(changed_files, review_config)

    return ReviewContext(
        pull_request=pull_request,
        changed_files=changed_files,
        rule_report=rule_report,
    )
