from app.schemas.code_context import CodeContext
from app.schemas.diff import PullRequestFile
from app.schemas.project_context import ProjectContext
from app.schemas.pull_request import PullRequestMetadata
from app.schemas.review import ReviewFinding, ReviewReport
from app.schemas.review_context import ReviewContext
from app.schemas.review_policy import ReviewPolicy
from app.services.prompt_builder import NOT_AVAILABLE, build_ai_review_prompt


def complete_context() -> ReviewContext:
    return ReviewContext(
        pull_request=PullRequestMetadata(
            number=42,
            title="Harden login flow",
            state="open",
            merged=False,
            author="developer",
            base_branch="main",
            head_branch="feature/login",
            commits=2,
            changed_files=1,
            additions=12,
            deletions=3,
            html_url="https://github.com/example/project/pull/42",
        ),
        changed_files=[
            PullRequestFile(
                filename="app/login.py",
                status="modified",
                additions=12,
                deletions=3,
                changes=15,
                patch="@@ -1 +1 @@\n-old\n+new",
            )
        ],
        rule_report=ReviewReport(
            risk_level="high",
            findings=[
                ReviewFinding(
                    rule_id="sensitive_file_changed",
                    severity="high",
                    message="A sensitive file changed.",
                    filename="app/login.py",
                )
            ],
            files_reviewed=1,
        ),
        project_context=ProjectContext(
            readme="# Login service",
            architecture="Layered architecture",
            contributing="Add tests for every change",
        ),
        code_context=CodeContext(
            changed_file_contents={
                "app/login.py": "def login():\n    return True",
            },
            related_test_contents={
                "tests/test_login.py": "def test_login():\n    assert login()",
            },
        ),
        review_policy=ReviewPolicy(
            review_focus=["security", "correctness"],
            custom_instructions="Check authentication boundaries.",
            severity_rules={"security": "high"},
            output_requirements=["必须指出文件位置"],
        ),
    )


def test_prompt_contains_all_review_context_sections() -> None:
    prompt = build_ai_review_prompt(complete_context())

    assert "senior software engineer and code reviewer" in prompt.system_prompt
    assert "Do not invent files" in prompt.system_prompt
    assert "AIReviewReport" in prompt.system_prompt

    review_input = prompt.review_input
    assert "=== REVIEW POLICY ===" in review_input
    assert 'review_focus: ["security","correctness"]' in review_input
    assert "Check authentication boundaries." in review_input
    assert 'severity_rules: {"security":"high"}' in review_input

    assert "=== PULL REQUEST ===" in review_input
    assert "number: 42" in review_input
    assert "title: Harden login flow" in review_input
    assert "author: developer" in review_input
    assert "base_branch: main" in review_input
    assert "head_branch: feature/login" in review_input

    assert "=== DETERMINISTIC RULE REPORT ===" in review_input
    assert "risk_level: high" in review_input
    assert '"rule_id":"sensitive_file_changed"' in review_input

    assert "=== PROJECT CONTEXT ===" in review_input
    assert "# Login service" in review_input
    assert "Layered architecture" in review_input
    assert "Add tests for every change" in review_input

    assert "=== CHANGED FILES AND PATCHES ===" in review_input
    assert "FILE: app/login.py" in review_input
    assert "@@ -1 +1 @@\n-old\n+new" in review_input

    assert "=== FULL CHANGED FILE CONTENTS ===" in review_input
    assert "def login():\n    return True" in review_input

    assert "=== RELATED TEST CONTENTS ===" in review_input
    assert "def test_login():\n    assert login()" in review_input


def test_missing_documents_patch_and_contents_use_placeholder() -> None:
    context = complete_context()
    context.project_context = ProjectContext()
    context.changed_files[0].patch = None
    context.code_context = CodeContext(
        changed_file_contents={},
        related_test_contents={},
    )

    prompt = build_ai_review_prompt(context)

    assert prompt.review_input.count(NOT_AVAILABLE) >= 5
    assert "--- README ---\n[not available]" in prompt.review_input
    assert "patch:\n[not available]" in prompt.review_input
    assert "=== FULL CHANGED FILE CONTENTS ===\n[not available]" in (
        prompt.review_input
    )
    assert "=== RELATED TEST CONTENTS ===\n[not available]" in (
        prompt.review_input
    )


def test_prompt_generation_is_stable_and_does_not_mutate_context() -> None:
    context = complete_context()
    before = context.model_dump()

    first = build_ai_review_prompt(context)
    second = build_ai_review_prompt(context)

    assert first == second
    assert context.model_dump() == before
