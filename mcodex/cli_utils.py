from __future__ import annotations

from pathlib import Path

from mcodex.config import find_repo_root, get_text_prefix, is_under_repo


def resolve_text_dir(text_dir: str | None) -> Path:
    """Resolve text directory.

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


def locate_text_dir_for_build(*, text: str | None, ref: str | None) -> tuple[Path, str]:
    """Locate a text directory and determine the ref selector for `mcodex build`.

    Interpretation:
      - ref == "." => working tree
      - otherwise => snapshot label

    Context-aware resolution:
      - Inside a text directory:
          mcodex build            -> (cwd, ".")
          mcodex build <ref>      -> (cwd, <ref>)
          mcodex build <text> <ref> -> (<text>, <ref>)
      - Inside a mcodex repo, outside a text directory:
          mcodex build <text>     -> (<text>, ".")
          mcodex build <text> <ref>
      - Outside a repo:
          <text> must be a path (existing directory containing metadata.yaml)
    """

    cwd = Path.cwd().expanduser().resolve()
    in_text_dir = (cwd / "metadata.yaml").exists()
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

    text_dir = _resolve_text_arg(text=arg1, cwd=cwd, in_repo=in_repo)
    return text_dir, arg2 or "."


def locate_text_dir_for_snapshot(
    *,
    text: str | None,
) -> Path:
    """Locate a text directory for `mcodex snapshot`.

    Rules:
      - Inside a text dir: `mcodex snapshot <label>`.
      - Inside a repo (anywhere): `mcodex snapshot <slug> <label>`.
      - Outside a repo: only path is accepted.

    The <slug> here is the *logical* slug (without the repo's text prefix).
    """

    cwd = Path.cwd().expanduser().resolve()
    in_text_dir = (cwd / "metadata.yaml").exists()

    if text is None:
        if not in_text_dir:
            raise FileNotFoundError(
                "No metadata.yaml found in current directory. "
                "Run this command inside a text directory, "
                "or specify <text> explicitly."
            )
        return cwd

    candidate = Path(text).expanduser()
    if candidate.exists():
        resolved = candidate.resolve()
        meta = resolved / "metadata.yaml"
        if not meta.exists():
            raise FileNotFoundError(f"No metadata.yaml found: {meta}")
        return resolved

    if not is_under_repo(cwd):
        raise FileNotFoundError(
            "Not in a mcodex repo. Outside a repo, <text> must be a path."
        )

    repo_root = find_repo_root(cwd)
    prefix = get_text_prefix(repo_root=repo_root)
    text_dir = (repo_root / f"{prefix}{text}").expanduser().resolve()
    meta = text_dir / "metadata.yaml"
    if not meta.exists():
        raise FileNotFoundError(
            f"No metadata.yaml found for slug '{text}'. Expected: {meta}"
        )
    return text_dir


def _resolve_text_arg(*, text: str, cwd: Path, in_repo: bool) -> Path:
    candidate = Path(text).expanduser()
    if candidate.exists():
        resolved = candidate.resolve()
        meta = resolved / "metadata.yaml"
        if not meta.exists():
            raise FileNotFoundError(f"No metadata.yaml found: {meta}")
        return resolved

    if not in_repo:
        raise FileNotFoundError(
            "Outside a mcodex repo, <text> must be a path to a text directory."
        )

    repo_root = find_repo_root(cwd)
    prefix = get_text_prefix(repo_root=repo_root)
    text_dir = (repo_root / f"{prefix}{text}").expanduser().resolve()
    meta = text_dir / "metadata.yaml"
    if not meta.exists():
        raise FileNotFoundError(
            f"No metadata.yaml found for text '{text}'. Expected: {meta}"
        )
    return text_dir
