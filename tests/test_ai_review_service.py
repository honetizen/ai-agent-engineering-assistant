from app.config.review_policy import DEFAULT_REVIEW_POLICY
from app.schemas.ai_prompt import AIReviewPrompt
from app.schemas.ai_review import AIReviewFinding, AIReviewReport
from app.schemas.code_context import CodeContext
from app.schemas.project_context import ProjectContext
from app.schemas.pull_request import PullRequestMetadata
from app.schemas.review import ReviewReport
from app.schemas.review_context import ReviewContext
from app.services.ai_review_service import review_context


def review_context_fixture() -> ReviewContext:
    return ReviewContext(
        pull_request=PullRequestMetadata(
            number=1,
            title="Add AI review skeleton",
            state="open",
            merged=False,
            author="developer",
            base_branch="main",
            head_branch="feature/ai-review",
            commits=1,
            changed_files=0,
            additions=0,
            deletions=0,
            html_url="https://github.com/example/project/pull/1",
        ),
        changed_files=[],
        rule_report=ReviewReport(
            risk_level="low",
            findings=[],
            files_reviewed=0,
        ),
        project_context=ProjectContext(),
        code_context=CodeContext(
            changed_file_contents={},
            related_test_contents={},
        ),
        review_policy=DEFAULT_REVIEW_POLICY,
    )


def test_default_provider_returns_mock_report() -> None:
    report = review_context(review_context_fixture())

    assert isinstance(report, AIReviewReport)
    assert report.summary == "Mock AI review completed"
    assert report.findings == []


def test_custom_provider_replaces_mock_provider() -> None:
    context = review_context_fixture()

    class CustomProvider:
        def __init__(self) -> None:
            self.received_prompt: AIReviewPrompt | None = None

        def review(self, received: AIReviewPrompt) -> AIReviewReport:
            self.received_prompt = received
            return AIReviewReport(
                summary="Custom review completed",
                findings=[
                    AIReviewFinding(
                        level="high",
                        file="app/main.py",
                        line=10,
                        issue="Example issue",
                        suggestion="Example suggestion",
                    )
                ],
            )

    provider = CustomProvider()
    report = review_context(context, provider=provider)

    assert isinstance(provider.received_prompt, AIReviewPrompt)
    assert "<REVIEW_POLICY>" in provider.received_prompt.review_input
    assert "Add AI review skeleton" in provider.received_prompt.review_input
    assert isinstance(report, AIReviewReport)
    assert report.summary == "Custom review completed"
    assert report.findings[0].level == "high"
