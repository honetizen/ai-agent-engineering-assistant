from pydantic import BaseModel, ConfigDict, Field


class PromptBuildConfig(BaseModel):
    """Read-only character budgets used while building an AI review prompt."""

    model_config = ConfigDict(frozen=True)

    max_project_document_chars: int = Field(default=12_000, gt=0)
    max_patch_chars_per_file: int = Field(default=12_000, gt=0)
    max_full_file_chars: int = Field(default=30_000, gt=0)
    max_related_test_chars: int = Field(default=20_000, gt=0)
    max_total_review_input_chars: int = Field(default=120_000, gt=0)


DEFAULT_PROMPT_BUILD_CONFIG = PromptBuildConfig()
