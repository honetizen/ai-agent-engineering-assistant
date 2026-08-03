from pydantic import BaseModel, Field


class PullRequestMetadata(BaseModel):
    """Selected metadata exposed for a GitHub pull request."""

    number: int
    title: str
    state: str
    merged: bool
    author: str
    base_branch: str
    head_branch: str
    base_sha: str = Field(min_length=1)
    head_sha: str = Field(min_length=1)
    base_repository: str = Field(min_length=1)
    head_repository: str = Field(min_length=1)
    commits: int
    changed_files: int
    additions: int
    deletions: int
    html_url: str
