from __future__ import annotations

import re

"""Shared constants used throughout mcodex.

This module defines constants, patterns, and default values
that are used across multiple modules to avoid duplication.
"""

# Snapshot label pattern (stage-number format like "draft-1", "rc-2")
SNAPSHOT_LABEL_PATTERN = re.compile(r"^(?P<stage>[a-z]+)-(?P<num>[0-9]+)$")

# Custom label pattern (alphanumeric, underscore, dot, hyphen)
CUSTOM_LABEL_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")

# Standard filenames
METADATA_FILENAME = "metadata.yaml"
TEXT_FILENAME = "text.md"
SNAPSHOT_DIR = ".snapshot"

# Snapshot stages in progression order
SNAPSHOT_STAGES = ["draft", "preview", "rc", "final", "published"]

__all__ = [
    "SNAPSHOT_LABEL_PATTERN",
    "CUSTOM_LABEL_PATTERN",
    "METADATA_FILENAME",
    "TEXT_FILENAME",
    "SNAPSHOT_DIR",
    "SNAPSHOT_STAGES",
]
