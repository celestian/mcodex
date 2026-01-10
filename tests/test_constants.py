from __future__ import annotations

from mcodex.constants import (
    CUSTOM_LABEL_PATTERN,
    METADATA_FILENAME,
    SNAPSHOT_DIR,
    SNAPSHOT_LABEL_PATTERN,
    SNAPSHOT_STAGES,
    TEXT_FILENAME,
)


def test_snapshot_label_pattern_matches_valid_labels() -> None:
    """Test SNAPSHOT_LABEL_PATTERN matches valid stage-number labels."""
    valid_labels = [
        "draft-1",
        "draft-10",
        "preview-2",
        "rc-5",
        "final-1",
        "published-1",
    ]

    for label in valid_labels:
        match = SNAPSHOT_LABEL_PATTERN.match(label)
        assert match is not None, f"Should match {label}"
        assert match.group("stage") in SNAPSHOT_STAGES or match.group("stage") in [
            "draft",
            "preview",
            "rc",
            "final",
            "published",
        ]
        assert match.group("num").isdigit()


def test_snapshot_label_pattern_rejects_invalid_labels() -> None:
    """Test SNAPSHOT_LABEL_PATTERN rejects invalid labels."""
    invalid_labels = [
        "draft",  # No number
        "1-draft",  # Wrong order
        "draft-",  # No number after dash
        "-1",  # No stage
        "DRAFT-1",  # Uppercase
        "draft_1",  # Underscore instead of dash
        "draft-1-extra",  # Extra parts
    ]

    for label in invalid_labels:
        match = SNAPSHOT_LABEL_PATTERN.match(label)
        assert match is None, f"Should not match {label}"


def test_custom_label_pattern_matches_valid_labels() -> None:
    """Test CUSTOM_LABEL_PATTERN matches valid custom labels."""
    valid_labels = [
        "draft-1",
        "sent-to-editor",
        "version_2.0",
        "final.revised",
        "RC1",
        "a",  # Single character
        "test123",
        "my_label-v1.0",
    ]

    for label in valid_labels:
        match = CUSTOM_LABEL_PATTERN.match(label)
        assert match is not None, f"Should match {label}"


def test_custom_label_pattern_rejects_invalid_labels() -> None:
    """Test CUSTOM_LABEL_PATTERN rejects invalid custom labels."""
    invalid_labels = [
        "-starts-with-dash",
        "_starts-with-underscore",
        ".starts-with-dot",
        "has space",
        "has/slash",
        "has\\backslash",
        "has@at",
        "has#hash",
        "",  # Empty
    ]

    for label in invalid_labels:
        match = CUSTOM_LABEL_PATTERN.match(label)
        assert match is None, f"Should not match '{label}'"


def test_snapshot_label_pattern_extracts_stage_and_number() -> None:
    """Test SNAPSHOT_LABEL_PATTERN extracts stage and number correctly."""
    label = "rc-42"
    match = SNAPSHOT_LABEL_PATTERN.match(label)

    assert match is not None
    assert match.group("stage") == "rc"
    assert match.group("num") == "42"


def test_snapshot_stages_has_correct_progression() -> None:
    """Test SNAPSHOT_STAGES contains expected stages in order."""
    expected = ["draft", "preview", "rc", "final", "published"]

    assert SNAPSHOT_STAGES == expected


def test_snapshot_stages_is_ordered() -> None:
    """Test SNAPSHOT_STAGES has progression order."""
    # Each stage should be "later" than the previous
    stages = SNAPSHOT_STAGES
    assert len(stages) == 5
    assert stages.index("draft") < stages.index("preview")
    assert stages.index("preview") < stages.index("rc")
    assert stages.index("rc") < stages.index("final")
    assert stages.index("final") < stages.index("published")


def test_filename_constants_are_strings() -> None:
    """Test filename constants are properly defined strings."""
    assert isinstance(METADATA_FILENAME, str)
    assert isinstance(TEXT_FILENAME, str)
    assert isinstance(SNAPSHOT_DIR, str)


def test_filename_constants_have_expected_values() -> None:
    """Test filename constants have expected values."""
    assert METADATA_FILENAME == "metadata.yaml"
    assert TEXT_FILENAME == "text.md"
    assert SNAPSHOT_DIR == ".snapshot"


def test_snapshot_dir_starts_with_dot() -> None:
    """Test SNAPSHOT_DIR is hidden directory (starts with dot)."""
    assert SNAPSHOT_DIR.startswith(".")
    assert not SNAPSHOT_DIR.startswith("..")
