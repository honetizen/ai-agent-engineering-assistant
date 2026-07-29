import os

import httpx

from app.schemas.diff import PullRequestFile
from app.schemas.pull_request import PullRequestMetadata


class GitHubNotFoundError(Exception):
    """Raised when GitHub cannot find the requested resource."""


class GitHubTimeoutError(Exception):
    """Raised when a request to GitHub times out."""


class GitHubUpstreamError(Exception):
    """Raised when GitHub returns an unexpected error."""


class GitHubClient:
    """Small asynchronous client for the GitHub REST API."""

    def __init__(
        self,
        token: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._token = token if token is not None else os.getenv("GITHUB_TOKEN")
        self._transport = transport

    async def get_pull_request(
        self,
        owner: str,
        repo: str,
        pull_number: int,
    ) -> PullRequestMetadata:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ai-github-engineering-assistant",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        try:
            async with httpx.AsyncClient(
                base_url="https://api.github.com",
                headers=headers,
                timeout=httpx.Timeout(30.0),
                transport=self._transport,
            ) as client:
                response = await client.get(
                    f"/repos/{owner}/{repo}/pulls/{pull_number}"
                )
        except httpx.TimeoutException as exc:
            raise GitHubTimeoutError from exc
        except httpx.RequestError as exc:
            raise GitHubUpstreamError from exc

        if response.status_code == 404:
            raise GitHubNotFoundError
        if response.is_error:
            raise GitHubUpstreamError

        try:
            data = response.json()
            return PullRequestMetadata(
                number=data["number"],
                title=data["title"],
                state=data["state"],
                merged=data["merged"],
                author=data["user"]["login"],
                base_branch=data["base"]["ref"],
                head_branch=data["head"]["ref"],
                commits=data["commits"],
                changed_files=data["changed_files"],
                additions=data["additions"],
                deletions=data["deletions"],
                html_url=data["html_url"],
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise GitHubUpstreamError from exc

    async def get_pull_request_files(
        self,
        owner: str,
        repo: str,
        pull_number: int,
    ) -> list[PullRequestFile]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ai-github-engineering-assistant",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"

        try:
            async with httpx.AsyncClient(
                base_url="https://api.github.com",
                headers=headers,
                timeout=httpx.Timeout(30.0),
                transport=self._transport,
            ) as client:
                response = await client.get(
                    f"/repos/{owner}/{repo}/pulls/{pull_number}/files"
                )
        except httpx.TimeoutException as exc:
            raise GitHubTimeoutError from exc
        except httpx.RequestError as exc:
            raise GitHubUpstreamError from exc

        if response.status_code == 404:
            raise GitHubNotFoundError
        if response.is_error:
            raise GitHubUpstreamError

        try:
            data = response.json()
            if not isinstance(data, list):
                raise TypeError
            return [
                PullRequestFile(
                    filename=file["filename"],
                    status=file["status"],
                    additions=file["additions"],
                    deletions=file["deletions"],
                    changes=file["changes"],
                    patch=file.get("patch"),
                )
                for file in data
            ]
        except (KeyError, TypeError, ValueError) as exc:
            raise GitHubUpstreamError from exc
