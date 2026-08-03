import json

from app.schemas.ai_prompt import AIReviewPrompt
from app.schemas.review_context import ReviewContext


NOT_AVAILABLE = "[not available]"
FILE_SEPARATOR = "=" * 72

SYSTEM_PROMPT = """You are a senior software engineer and code reviewer.

Review the supplied project information and code changes. Focus on the areas
listed in REVIEW POLICY, including correctness, security, architecture, and
tests when those areas are requested.

Evidence requirements:
- Base every conclusion only on the supplied context.
- Do not invent files, functions, behavior, or project rules.
- Explicitly state when the available information is insufficient.
- Treat deterministic rule findings as review signals, not unconditional proof
  that the code is incorrect.

Return a single object compatible with AIReviewReport. It must contain:
- summary
- findings

Every finding must contain:
- level: low, medium, or high
- file
- line: an integer or null
- issue
- suggestion

Do not wrap the output in a Markdown code fence."""


def build_ai_review_prompt(context: ReviewContext) -> AIReviewPrompt:
    """Convert a ReviewContext into deterministic, structured model input."""
    sections = [
        _review_policy_section(context),
        _pull_request_section(context),
        _rule_report_section(context),
        _project_context_section(context),
        _changed_files_section(context),
        _content_section(
            "FULL CHANGED FILE CONTENTS",
            context.code_context.changed_file_contents,
        ),
        _content_section(
            "RELATED TEST CONTENTS",
            context.code_context.related_test_contents,
        ),
    ]
    return AIReviewPrompt(
        system_prompt=SYSTEM_PROMPT,
        review_input="\n\n".join(sections),
    )


def _review_policy_section(context: ReviewContext) -> str:
    policy = context.review_policy
    return "\n".join(
        [
            "=== REVIEW POLICY ===",
            f"review_focus: {_as_json(policy.review_focus)}",
            "custom_instructions:",
            policy.custom_instructions or NOT_AVAILABLE,
            f"severity_rules: {_as_json(policy.severity_rules)}",
            f"output_requirements: {_as_json(policy.output_requirements)}",
        ]
    )


def _pull_request_section(context: ReviewContext) -> str:
    pull_request = context.pull_request
    return "\n".join(
        [
            "=== PULL REQUEST ===",
            f"number: {pull_request.number}",
            f"title: {pull_request.title}",
            f"author: {pull_request.author}",
            f"base_branch: {pull_request.base_branch}",
            f"head_branch: {pull_request.head_branch}",
            f"commits: {pull_request.commits}",
            f"changed_files: {pull_request.changed_files}",
            f"additions: {pull_request.additions}",
            f"deletions: {pull_request.deletions}",
        ]
    )


def _rule_report_section(context: ReviewContext) -> str:
    report = context.rule_report
    findings = [finding.model_dump() for finding in report.findings]
    return "\n".join(
        [
            "=== DETERMINISTIC RULE REPORT ===",
            f"risk_level: {report.risk_level}",
            f"findings: {_as_json(findings)}",
        ]
    )


def _project_context_section(context: ReviewContext) -> str:
    project = context.project_context
    return "\n".join(
        [
            "=== PROJECT CONTEXT ===",
            "--- README ---",
            project.readme if project.readme is not None else NOT_AVAILABLE,
            "--- ARCHITECTURE ---",
            (
                project.architecture
                if project.architecture is not None
                else NOT_AVAILABLE
            ),
            "--- CONTRIBUTING ---",
            (
                project.contributing
                if project.contributing is not None
                else NOT_AVAILABLE
            ),
        ]
    )


def _changed_files_section(context: ReviewContext) -> str:
    blocks = []
    for file in context.changed_files:
        patch = file.patch if file.patch is not None else NOT_AVAILABLE
        blocks.append(
            "\n".join(
                [
                    FILE_SEPARATOR,
                    f"FILE: {file.filename}",
                    f"status: {file.status}",
                    f"additions: {file.additions}",
                    f"deletions: {file.deletions}",
                    "patch:",
                    patch,
                    FILE_SEPARATOR,
                ]
            )
        )
    body = "\n".join(blocks) if blocks else NOT_AVAILABLE
    return f"=== CHANGED FILES AND PATCHES ===\n{body}"


def _content_section(title: str, contents: dict[str, str]) -> str:
    blocks = []
    for filename in sorted(contents):
        blocks.append(
            "\n".join(
                [
                    FILE_SEPARATOR,
                    f"FILE: {filename}",
                    contents[filename],
                    FILE_SEPARATOR,
                ]
            )
        )
    body = "\n".join(blocks) if blocks else NOT_AVAILABLE
    return f"=== {title} ===\n{body}"


def _as_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
