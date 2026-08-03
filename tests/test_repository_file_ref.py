import asyncio
import base64

import httpx

from app.services.github_client import GitHubClient


def test_get_repository_file_sends_encoded_path_and_ref_query() -> None:
    expected_content = "# Version-pinned guide"

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path.endswith("/contents/docs/My Guide?#.md")
        assert b"My%20Guide%3F%23.md" in request.url.raw_path
        assert request.url.params["ref"] == "refs/pull/1/head"
        encoded = base64.b64encode(expected_content.encode()).decode()
        return httpx.Response(
            200,
            json={"encoding": "base64", "content": encoded},
        )

    client = GitHubClient(
        token="test-token",
        transport=httpx.MockTransport(handler),
    )
    content = asyncio.run(
        client.get_repository_file(
            "example",
            "project",
            "docs/My Guide?#.md",
            ref="refs/pull/1/head",
        )
    )

    assert content == expected_content


def test_get_repository_file_without_ref_omits_query_parameter() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "ref" not in request.url.params
        encoded = base64.b64encode(b"content").decode()
        return httpx.Response(
            200,
            json={"encoding": "base64", "content": encoded},
        )

    client = GitHubClient(transport=httpx.MockTransport(handler))

    assert asyncio.run(
        client.get_repository_file("example", "project", "README.md")
    ) == "content"
