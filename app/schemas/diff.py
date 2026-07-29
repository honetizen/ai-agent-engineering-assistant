from pydantic import BaseModel


class PullRequestFile(BaseModel):
    """Selected change data for a file in a GitHub pull request."""

    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    patch: str | None = None
