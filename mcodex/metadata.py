from __future__ import annotations

from pathlib import Path
from typing import Any

from mcodex.yaml_utils import safe_dump_yaml, safe_load_yaml

LATEST_METADATA_VERSION = 1


def load_metadata(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Metadata file not found: {path}")

    data = safe_load_yaml(path)

    upgraded, changed = upgrade_metadata(data)
    if changed:
        write_metadata(path, upgraded)

    return upgraded


def write_metadata(path: Path, data: dict[str, Any]) -> None:
    safe_dump_yaml(data, path)


def upgrade_metadata(data: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """
    Upgrade metadata dict to the latest version.

    Returns:
        (upgraded_data, changed)
    """
    changed = False
    version = data.get("metadata_version")

    if version is None:
        data = _upgrade_0_to_1(data)
        changed = True
        version = data.get("metadata_version")

    if version != LATEST_METADATA_VERSION:
        raise ValueError(
            f"Unsupported metadata_version: {version} "
            f"(latest is {LATEST_METADATA_VERSION})"
        )

    return data, changed


def _upgrade_0_to_1(data: dict[str, Any]) -> dict[str, Any]:
    upgraded = dict(data)
    upgraded["metadata_version"] = 1
    if "authors" not in upgraded or upgraded["authors"] is None:
        upgraded["authors"] = []
    return upgraded
