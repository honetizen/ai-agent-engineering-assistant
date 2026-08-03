import pytest

from app.services.repository import split_repository_full_name


def test_split_repository_full_name() -> None:
    assert split_repository_full_name("company/project") == (
        "company",
        "project",
    )


@pytest.mark.parametrize(
    "full_name",
    [
        "",
        "project",
        "/project",
        "company/",
        "company/project/extra",
        " company/project",
    ],
)
def test_split_repository_full_name_rejects_invalid_format(
    full_name: str,
) -> None:
    with pytest.raises(ValueError, match="repository full name"):
        split_repository_full_name(full_name)
