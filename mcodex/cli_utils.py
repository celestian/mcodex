from __future__ import annotations

from pathlib import Path

from mcodex.config import find_repo_root, get_text_prefix, is_under_repo
from mcodex.path_utils import get_metadata_path, normalize_path


def resolve_text_dir(text_dir: str | None) -> Path:
    """Resolve a text directory for commands like `mcodex status`.

    If `text_dir` is provided, it can be either:
      - a path to a text directory (must contain metadata.yaml), or
      - a slug (without text prefix) when inside a mcodex repo.

    If `text_dir` is None, this uses the current working directory, but only if
    it contains metadata.yaml.
    """
    cwd = normalize_path(Path.cwd())

    if text_dir is None:
        meta = get_metadata_path(cwd)
        if not meta.exists():
            raise FileNotFoundError(
                "No metadata.yaml found in current directory. "
                "Run this command inside a text directory or "
                "specify <text_dir> explicitly."
            )
        return cwd

    return _resolve_text_arg(
        text=text_dir,
        cwd=cwd,
        in_repo=is_under_repo(cwd),
        arg_name="<text_dir>",
        outside_repo_message=(
            "Outside a mcodex repo, <text_dir> must be a path to a text directory."
        ),
        not_found_template="No metadata.yaml found for text '{text}'. Expected: {meta}",
    )


def locate_text_dir_for_build(*, text: str | None, ref: str | None) -> tuple[Path, str]:
    """Locate a text directory and determine the ref selector for `mcodex build`."""

    cwd = normalize_path(Path.cwd())
    in_text_dir = _is_text_dir(cwd)
    in_repo = is_under_repo(cwd)

    arg1 = (text or "").strip() or None
    arg2 = (ref or "").strip() or None

    if arg1 is None and arg2 is None:
        if not in_text_dir:
            raise FileNotFoundError(
                "Run this command inside a text directory, "
                "or specify <text> explicitly."
            )
        return cwd, "."

    if in_text_dir and arg1 is not None and arg2 is None:
        # One arg inside a text dir is always <ref>.
        return cwd, arg1

    if arg1 is None:
        # Only <ref> given, but not in a text dir.
        raise FileNotFoundError(
            "Outside a text directory, you must also specify <text>."
        )

    text_dir = _resolve_text_arg(
        text=arg1,
        cwd=cwd,
        in_repo=in_repo,
        arg_name="<text>",
        outside_repo_message=(
            "Outside a mcodex repo, <text> must be a path to a text directory."
        ),
        not_found_template="No metadata.yaml found for text '{text}'. Expected: {meta}",
    )
    return text_dir, arg2 or "."


def locate_text_dir_for_snapshot(*, text: str | None) -> Path:
    """Locate a text directory for `mcodex snapshot`."""

    cwd = normalize_path(Path.cwd())
    in_text_dir = _is_text_dir(cwd)
    in_repo = is_under_repo(cwd)

    if text is None:
        if not in_text_dir:
            raise FileNotFoundError(
                "No metadata.yaml found in current directory. "
                "Run this command inside a text directory, "
                "or specify <text> explicitly."
            )
        return cwd

    return _resolve_text_arg(
        text=text,
        cwd=cwd,
        in_repo=in_repo,
        arg_name="<text>",
        outside_repo_message=(
            "Not in a mcodex repo. Outside a repo, <text> must be a path."
        ),
        not_found_template="No metadata.yaml found for slug '{text}'. Expected: {meta}",
    )


def _is_text_dir(path: Path) -> bool:
    return get_metadata_path(path).is_file()


def _resolve_text_arg(
    *,
    text: str,
    cwd: Path,
    in_repo: bool,
    arg_name: str,
    outside_repo_message: str,
    not_found_template: str,
) -> Path:
    candidate = Path(text).expanduser()

    # Path form
    if candidate.exists():
        resolved = normalize_path(candidate)
        meta = get_metadata_path(resolved)
        if not meta.exists():
            raise FileNotFoundError(f"No metadata.yaml found: {meta}")
        return resolved

    # Slug form (only inside repo)
    if not in_repo:
        raise FileNotFoundError(outside_repo_message)

    repo_root = find_repo_root(cwd)
    prefix = get_text_prefix(repo_root=repo_root)
    text_dir = normalize_path(repo_root / f"{prefix}{text}")
    meta = get_metadata_path(text_dir)

    if not meta.exists():
        raise FileNotFoundError(not_found_template.format(text=text, meta=meta))

    return text_dir
