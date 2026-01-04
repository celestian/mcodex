from __future__ import annotations

import shutil
from collections.abc import Iterable
from pathlib import Path

TEST_ROOT_MARKER = ".mcodex-test-root"


def ensure_test_root_marker(root: Path) -> Path:
    """Create a marker file that identifies a directory as a safe test root."""

    root = root.expanduser().resolve()
    marker = root / TEST_ROOT_MARKER
    marker.write_text("mcodex test root\n", encoding="utf-8")
    return marker


def _find_marked_root(path: Path, marker_name: str) -> Path | None:
    resolved = path.expanduser().resolve()
    for parent in [resolved, *resolved.parents]:
        if (parent / marker_name).exists():
            return parent
    return None


def _is_under_any_root(path: Path, roots: Iterable[Path]) -> bool:
    resolved = path.expanduser().resolve()
    for root in roots:
        r = root.expanduser().resolve()
        try:
            resolved.relative_to(r)
        except ValueError:
            continue
        return True
    return False


def safe_rmtree(
    path: Path,
    *,
    allowed_roots: Iterable[Path] | None = None,
    marker_name: str | None = None,
    ignore_errors: bool = False,
) -> None:
    """Remove a directory tree with strong safety checks.

    Deletion is allowed only if at least one of the following is true:
    - marker_name is provided AND the path is under a directory containing it
    - allowed_roots is provided AND the path is under one of allowed_roots

    This design forces production code to pass allowed_roots explicitly.
    Tests may use marker_name with a dedicated marker file.
    """

    resolved = path.expanduser().resolve()

    if not resolved.exists():
        return

    if resolved == Path("/") or resolved == Path.home().resolve():
        raise RuntimeError(f"Refusing to delete unsafe path: {resolved}")

    ok = False

    if marker_name is not None:
        if _find_marked_root(resolved, marker_name) is not None:
            ok = True

    if not ok:
        if allowed_roots is None:
            raise RuntimeError(
                "Refusing to delete path without safety context: "
                f"{resolved} (marker_name={marker_name}, allowed_roots=None)"
            )
        ok = _is_under_any_root(resolved, allowed_roots)

    if not ok:
        raise RuntimeError(
            "Refusing to delete path outside of allowed roots: "
            f"{resolved} (allowed_roots={list(allowed_roots or [])})"
        )

    shutil.rmtree(resolved, ignore_errors=ignore_errors)
