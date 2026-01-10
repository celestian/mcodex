from __future__ import annotations

from pathlib import Path

import pytest

from mcodex.path_utils import get_metadata_path, get_snapshot_dir, normalize_path


def test_normalize_path_with_absolute_path(tmp_path: Path) -> None:
    """Test normalize_path with an already absolute path."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    result = normalize_path(test_dir)

    assert result == test_dir.resolve()
    assert result.is_absolute()


def test_normalize_path_with_relative_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test normalize_path with a relative path."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()
    monkeypatch.chdir(test_dir)

    relative = Path(".")
    result = normalize_path(relative)

    assert result == test_dir.resolve()
    assert result.is_absolute()


def test_normalize_path_with_home_expansion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test normalize_path expands ~ to home directory."""
    # Mock home directory
    home_dir = tmp_path / "home"
    home_dir.mkdir()
    monkeypatch.setenv("HOME", str(home_dir))

    path_with_tilde = Path("~/test")
    result = normalize_path(path_with_tilde)

    assert str(result).startswith(str(home_dir))
    assert "~" not in str(result)


def test_normalize_path_with_symlink(tmp_path: Path) -> None:
    """Test normalize_path resolves symlinks."""
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    symlink = tmp_path / "link"
    symlink.symlink_to(real_dir)

    result = normalize_path(symlink)

    assert result == real_dir.resolve()
    assert not result.is_symlink()


def test_get_metadata_path_returns_correct_path(tmp_path: Path) -> None:
    """Test get_metadata_path returns metadata.yaml in text directory."""
    text_dir = tmp_path / "my_text"

    result = get_metadata_path(text_dir)

    assert result == text_dir / "metadata.yaml"
    assert result.name == "metadata.yaml"


def test_get_metadata_path_with_nested_directory(tmp_path: Path) -> None:
    """Test get_metadata_path with nested directories."""
    text_dir = tmp_path / "project" / "texts" / "my_text"

    result = get_metadata_path(text_dir)

    assert result == text_dir / "metadata.yaml"
    assert result.parent == text_dir


def test_get_snapshot_dir_returns_correct_path(tmp_path: Path) -> None:
    """Test get_snapshot_dir returns .snapshot directory."""
    text_dir = tmp_path / "my_text"

    result = get_snapshot_dir(text_dir)

    assert result == text_dir / ".snapshot"
    assert result.name == ".snapshot"


def test_get_snapshot_dir_with_absolute_path(tmp_path: Path) -> None:
    """Test get_snapshot_dir with absolute path."""
    text_dir = tmp_path / "texts" / "article"

    result = get_snapshot_dir(text_dir)

    assert result == text_dir / ".snapshot"
    assert result.parent == text_dir


def test_normalize_path_idempotent(tmp_path: Path) -> None:
    """Test that normalizing twice gives same result."""
    test_dir = tmp_path / "test"
    test_dir.mkdir()

    first = normalize_path(test_dir)
    second = normalize_path(first)

    assert first == second
