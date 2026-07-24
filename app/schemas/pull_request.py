from pydantic import BaseModel


class PullRequestMetadata(BaseModel):
    """Selected metadata exposed for a GitHub pull request."""

    number: int
    title: str
    state: str
    merged: bool
    author: str
    base_branch: str
    head_branch: str
    commits: int
    changed_files: int
    additions: int
    deletions: int
    html_url: str
