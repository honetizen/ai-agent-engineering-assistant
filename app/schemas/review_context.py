from pydantic import BaseModel

from app.schemas.diff import PullRequestFile
from app.schemas.project_context import ProjectContext
from app.schemas.pull_request import PullRequestMetadata
from app.schemas.review import ReviewReport


class ReviewContext(BaseModel):
    """Complete internal input package for reviewing a pull request."""

    pull_request: PullRequestMetadata
    changed_files: list[PullRequestFile]
    rule_report: ReviewReport
    project_context: ProjectContext
