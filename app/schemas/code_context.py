from pydantic import BaseModel


class CodeContext(BaseModel):
    """Full changed-file and conventionally related test-file contents."""

    changed_file_contents: dict[str, str]
    related_test_contents: dict[str, str]
