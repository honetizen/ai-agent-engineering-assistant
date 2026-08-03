from fastapi import APIRouter, Depends, HTTPException, status

from app.exceptions.ai_provider import (
    AIProviderConfigurationError,
    AIProviderError,
    AIProviderResponseError,
    AIProviderTimeoutError,
)
from app.schemas.ai_review import AIReviewReport
from app.schemas.diff import PullRequestFile
from app.schemas.pull_request import PullRequestMetadata
from app.schemas.review import ReviewReport
from app.schemas.review_context import ReviewContext
from app.services.github_client import (
    GitHubClient,
    GitHubNotFoundError,
    GitHubTimeoutError,
    GitHubUpstreamError,
)
from app.services.ai_review_service import review_context as run_ai_review
from app.services.openai_provider import create_openai_provider
from app.services.review_context_service import build_review_context
from app.services.review_service import review_pull_request


router = APIRouter(prefix="/github", tags=["github"])


def get_github_client() -> GitHubClient:
    return GitHubClient()


@router.get(
    "/repos/{owner}/{repo}/pulls/{pull_number}/ai-review",
    response_model=AIReviewReport,
)
async def get_pull_request_ai_review(
    owner: str,
    repo: str,
    pull_number: int,
    github_client: GitHubClient = Depends(get_github_client),
) -> AIReviewReport:
    try:
        context = await build_review_context(
            owner,
            repo,
            pull_number,
            github_client=github_client,
        )
        return await run_ai_review(context)
    except GitHubNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pull request not found",
        ) from None
    except GitHubTimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="GitHub request timed out",
        ) from None
    except GitHubUpstreamError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="GitHub request failed",
        ) from None


@router.post(
    "/repos/{owner}/{repo}/pulls/{pull_number}/ai-review/openai",
    response_model=AIReviewReport,
)
async def get_pull_request_openai_review(
    owner: str,
    repo: str,
    pull_number: int,
    github_client: GitHubClient = Depends(get_github_client),
) -> AIReviewReport:
    try:
        context = await build_review_context(
            owner,
            repo,
            pull_number,
            github_client=github_client,
        )
        provider = create_openai_provider()
        return await run_ai_review(context, provider=provider)
    except GitHubNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pull request not found",
        ) from None
    except GitHubTimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="GitHub request timed out",
        ) from None
    except GitHubUpstreamError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="GitHub request failed",
        ) from None
    except AIProviderConfigurationError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI provider is not configured",
        ) from None
    except AIProviderTimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI provider request timed out",
        ) from None
    except AIProviderResponseError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI provider response failed",
        ) from None
    except AIProviderError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI provider request failed",
        ) from None


@router.get(
    "/repos/{owner}/{repo}/pulls/{pull_number}/context",
    response_model=ReviewContext,
)
async def get_pull_request_context(
    owner: str,
    repo: str,
    pull_number: int,
    github_client: GitHubClient = Depends(get_github_client),
) -> ReviewContext:
    try:
        return await build_review_context(
            owner,
            repo,
            pull_number,
            github_client=github_client,
        )
    except GitHubNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pull request not found",
        ) from None
    except GitHubTimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="GitHub request timed out",
        ) from None
    except GitHubUpstreamError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="GitHub request failed",
        ) from None


@router.get(
    "/repos/{owner}/{repo}/pulls/{pull_number}/review",
    response_model=ReviewReport,
)
async def review_pull_request_endpoint(
    owner: str,
    repo: str,
    pull_number: int,
    github_client: GitHubClient = Depends(get_github_client),
) -> ReviewReport:
    try:
        files = await github_client.get_pull_request_files(
            owner,
            repo,
            pull_number,
        )
        return review_pull_request(files)
    except GitHubNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pull request not found",
        ) from None
    except GitHubTimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="GitHub request timed out",
        ) from None
    except GitHubUpstreamError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="GitHub request failed",
        ) from None


@router.get(
    "/repos/{owner}/{repo}/pulls/{pull_number}/files",
    response_model=list[PullRequestFile],
)
async def get_pull_request_files(
    owner: str,
    repo: str,
    pull_number: int,
    github_client: GitHubClient = Depends(get_github_client),
) -> list[PullRequestFile]:
    try:
        return await github_client.get_pull_request_files(owner, repo, pull_number)
    except GitHubNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pull request not found",
        ) from None
    except GitHubTimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="GitHub request timed out",
        ) from None
    except GitHubUpstreamError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="GitHub request failed",
        ) from None


@router.get(
    "/repos/{owner}/{repo}/pulls/{pull_number}",
    response_model=PullRequestMetadata,
)
async def get_pull_request(
    owner: str,
    repo: str,
    pull_number: int,
    github_client: GitHubClient = Depends(get_github_client),
) -> PullRequestMetadata:
    try:
        return await github_client.get_pull_request(owner, repo, pull_number)
    except GitHubNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pull request not found",
        ) from None
    except GitHubTimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="GitHub request timed out",
        ) from None
    except GitHubUpstreamError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="GitHub request failed",
        ) from None
