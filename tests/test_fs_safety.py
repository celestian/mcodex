from __future__ import annotations

from pathlib import Path

import pytest

from mcodex.services.fs import TEST_ROOT_MARKER, ensure_test_root_marker, safe_rmtree


def test_safe_rmtree_refuses_without_marker(tmp_path: Path) -> None:
    d = tmp_path / "unmarked"
    d.mkdir()

    with pytest.raises(RuntimeError):
        safe_rmtree(d)


def test_safe_rmtree_allows_marked_root(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    ensure_test_root_marker(root)

    child = root / "child"
    child.mkdir()

    safe_rmtree(child, marker_name=TEST_ROOT_MARKER)
    assert not child.exists()


def test_safe_rmtree_allows_deleting_under_marked_root(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    ensure_test_root_marker(root)

    nested = root / "a" / "b" / "c"
    nested.mkdir(parents=True)

    safe_rmtree(root / "a", marker_name=TEST_ROOT_MARKER)
    assert not (root / "a").exists()


def test_safe_rmtree_allows_allowed_roots_without_marker(tmp_path: Path) -> None:
    root = tmp_path / "allowed"
    root.mkdir()

    target = root / "x"
    target.mkdir()

    safe_rmtree(target, allowed_roots=[root], marker_name=TEST_ROOT_MARKER)
    assert not target.exists()
