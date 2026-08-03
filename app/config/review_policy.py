from app.schemas.review_policy import ReviewPolicy


DEFAULT_REVIEW_POLICY = ReviewPolicy(
    review_focus=[
        "correctness",
        "security",
        "architecture",
        "test",
    ],
    custom_instructions=None,
    severity_rules={
        "security": "high",
        "architecture": "medium",
    },
    output_requirements=[
        "必须指出文件位置",
        "必须提供修改建议",
    ],
)
