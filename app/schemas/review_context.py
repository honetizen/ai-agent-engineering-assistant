from pydantic import BaseModel

from app.schemas.code_context import CodeContext
from app.schemas.diff import PullRequestFile
from app.schemas.project_context import ProjectContext
from app.schemas.pull_request import PullRequestMetadata
from app.schemas.review import ReviewReport
from app.schemas.review_policy import ReviewPolicy


class ReviewContext(BaseModel):
    """Complete internal input package for reviewing a pull request."""

    pull_request: PullRequestMetadata
    changed_files: list[PullRequestFile]
    rule_report: ReviewReport
    project_context: ProjectContext
    code_context: CodeContext
    review_policy: ReviewPolicy
