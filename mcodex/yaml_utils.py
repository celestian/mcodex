from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

"""YAML utility functions.

This module provides safe YAML loading and dumping operations
with consistent error handling and defaults.
"""


def safe_load_yaml(path: Path) -> dict[str, Any]:
    """Load YAML file safely, always returning a dict.

    This function loads YAML content and ensures the result is a dictionary.
    Empty files return an empty dict. Non-dict content raises an error.

    Args:
        path: Path to YAML file

    Returns:
        Dict loaded from YAML, or empty dict if file is empty

    Raises:
        ValueError: If YAML contains non-dict data (e.g., list, scalar)
        FileNotFoundError: If file doesn't exist

    Example:
        >>> safe_load_yaml(Path("config.yaml"))
        {'key': 'value'}
    """
    content = path.read_text(encoding="utf-8")
    data = yaml.safe_load(content) or {}

    if not isinstance(data, dict):
        raise ValueError(
            f"Invalid YAML in {path}: expected mapping, got {type(data).__name__}"
        )

    return data


def safe_dump_yaml(data: dict[str, Any], path: Path) -> None:
    """Write dict to YAML file safely.

    Writes YAML with consistent formatting:
    - Keys in original order (not sorted)
    - Unicode characters preserved
    - UTF-8 encoding

    Args:
        data: Dict to write
        path: Target YAML file path

    Example:
        >>> safe_dump_yaml({'name': 'test'}, Path("output.yaml"))
    """
    yaml_str = yaml.safe_dump(
        data,
        sort_keys=False,
        allow_unicode=True,
    )
    path.write_text(yaml_str, encoding="utf-8")


__all__ = [
    "safe_load_yaml",
    "safe_dump_yaml",
]
