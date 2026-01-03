from __future__ import annotations

from pathlib import Path


def resolve_text_dir(text_dir: str | None) -> Path:
    """
    Resolve text directory.

    If text_dir is provided, use it.
    Otherwise, use current working directory, but only if it
    contains metadata.yaml.

    Raises:
        FileNotFoundError if metadata.yaml is missing.
    """
    if text_dir is not None:
        return Path(text_dir)

    cwd = Path.cwd()
    meta = cwd / "metadata.yaml"
    if not meta.exists():
        raise FileNotFoundError(
            "No metadata.yaml found in current directory. "
            "Run this command inside a text directory or "
            "specify <text_dir> explicitly."
        )
    return cwd
