from pydantic import BaseModel


class ProjectContext(BaseModel):
    """Selected repository documentation used as review context."""

    readme: str | None = None
    architecture: str | None = None
    contributing: str | None = None
