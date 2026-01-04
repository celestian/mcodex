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


def locate_text_dir(
    *,
    root: Path,
    slug: str | None,
    version: str | None,
) -> tuple[Path, str]:
    """Locate a text directory and determine the version selector.

    Rules:
      - Inside a text dir: `mcodex build [<version>]`.
      - From a root: `mcodex build <slug> [<version>]`.

    With docopt, a single positional argument is parsed as <slug>.
    If we are already inside a text directory, we reinterpret <slug>
    as <version>.

    Returns:
        (text_dir, version) where version is '.' or a snapshot label.
    """
    root = root.expanduser().resolve()

    arg1 = slug
    arg2 = version

    cwd = Path.cwd().expanduser().resolve()
    in_text_dir = (cwd / "metadata.yaml").exists()

    if arg1 is None and arg2 is None:
        if not in_text_dir:
            raise FileNotFoundError(
                "No metadata.yaml found in current directory. "
                "Run this command inside a text directory or "
                "specify <slug> (and optionally --root)."
            )
        return cwd, "."

    if arg1 is not None and arg2 is None:
        if in_text_dir:
            return cwd, arg1
        return _resolve_text_dir_from_root(root=root, slug=arg1), "."

    if arg1 is None and arg2 is not None:
        if not in_text_dir:
            raise FileNotFoundError(
                "No metadata.yaml found in current directory. "
                "Run this command inside a text directory or "
                "specify <slug> (and optionally --root)."
            )
        return cwd, arg2

    assert arg1 is not None
    assert arg2 is not None
    return _resolve_text_dir_from_root(root=root, slug=arg1), arg2


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


def _resolve_text_dir_from_root(*, root: Path, slug: str) -> Path:
    if not root.exists():
        raise FileNotFoundError(f"Root directory does not exist: {root}")
    if not root.is_dir():
        raise NotADirectoryError(f"Root path is not a directory: {root}")

    text_dir = (root / slug).expanduser().resolve()
    meta = text_dir / "metadata.yaml"

    if not meta.exists():
        raise FileNotFoundError(
            f"No metadata.yaml found for slug '{slug}'. Expected: {meta}"
        )

    return text_dir
