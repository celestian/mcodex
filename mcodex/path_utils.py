from __future__ import annotations

from pathlib import Path

"""Path utility functions.

This module provides common path operations used throughout mcodex,
including path normalization and standard path construction.
"""


def normalize_path(path: Path) -> Path:
    """Normalize a path by expanding user home and resolving symlinks.

    This function ensures that paths are fully resolved, absolute,
    and have user home directories (~) expanded.

    Args:
        path: Path to normalize

    Returns:
        Fully resolved absolute path

    Example:
        >>> normalize_path(Path("~/project"))
        PosixPath('/home/user/project')
    """
    return path.expanduser().resolve()


def get_metadata_path(text_dir: Path) -> Path:
    """Get the metadata.yaml path for a text directory.

    Args:
        text_dir: Text directory path

    Returns:
        Path to metadata.yaml file

    Example:
        >>> get_metadata_path(Path("my_text"))
        PosixPath('my_text/metadata.yaml')
    """
    return text_dir / "metadata.yaml"


def get_snapshot_dir(text_dir: Path) -> Path:
    """Get the snapshot directory path for a text directory.

    Args:
        text_dir: Text directory path

    Returns:
        Path to .snapshot directory

    Example:
        >>> get_snapshot_dir(Path("my_text"))
        PosixPath('my_text/.snapshot')
    """
    return text_dir / ".snapshot"


__all__ = [
    "normalize_path",
    "get_metadata_path",
    "get_snapshot_dir",
]
