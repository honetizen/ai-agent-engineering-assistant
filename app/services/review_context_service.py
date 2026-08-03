from app.config.review_policy import DEFAULT_REVIEW_POLICY
from app.config.review_config import ReviewRuleConfig
from app.schemas.review_context import ReviewContext
from app.schemas.review_policy import ReviewPolicy
from app.services.code_context_service import build_code_context
from app.services.github_client import GitHubClient
from app.services.project_context_service import get_project_context
from app.services.review_service import review_pull_request


async def build_review_context(
    owner: str,
    repo: str,
    pull_number: int,
    github_client: GitHubClient | None = None,
    review_config: ReviewRuleConfig | None = None,
    review_policy: ReviewPolicy | None = None,
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
    project_context = await get_project_context(
        pull_request.base_repository,
        pull_request.base_sha,
        github_client=client,
    )
    code_context = await build_code_context(
        pull_request.head_repository,
        pull_request.head_sha,
        changed_files,
        github_client=client,
    )
    active_review_policy = (
        review_policy
        if review_policy is not None
        else DEFAULT_REVIEW_POLICY.model_copy(deep=True)
    )

    return ReviewContext(
        pull_request=pull_request,
        changed_files=changed_files,
        rule_report=rule_report,
        project_context=project_context,
        code_context=code_context,
        review_policy=active_review_policy,
    )
