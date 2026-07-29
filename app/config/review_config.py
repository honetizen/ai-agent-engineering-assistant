from pydantic import BaseModel, Field, field_validator


class ReviewRuleConfig(BaseModel):
    """Project-specific settings used by deterministic review rules."""

    business_extensions: list[str] = Field(default_factory=lambda: [".py"])
    test_directories: list[str] = Field(default_factory=lambda: ["tests/"])
    sensitive_patterns: list[str] = Field(
        default_factory=lambda: [
            ".env",
            "secret",
            "credential",
            "token",
            "key",
            "settings",
            "config",
        ]
    )
    max_files: int = Field(default=10, gt=0)
    max_changes: int = Field(default=300, gt=0)

    @field_validator(
        "business_extensions",
        "test_directories",
        "sensitive_patterns",
        mode="before",
    )
    @classmethod
    def normalize_matching_values(cls, values: list[str]) -> list[str]:
        """Normalize configurable matching values for case-insensitive rules."""
        return [
            value.replace("\\", "/").lower()
            for value in values
        ]


DEFAULT_REVIEW_CONFIG = ReviewRuleConfig()
