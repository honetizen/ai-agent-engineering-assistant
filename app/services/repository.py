def split_repository_full_name(full_name: str) -> tuple[str, str]:
    """Split GitHub's canonical owner/repository name or reject it."""
    if full_name != full_name.strip():
        raise ValueError("repository full name must not contain outer whitespace")
    parts = full_name.split("/")
    if len(parts) != 2 or not all(parts):
        raise ValueError(
            "repository full name must use the format 'owner/repository'"
        )
    return parts[0], parts[1]
