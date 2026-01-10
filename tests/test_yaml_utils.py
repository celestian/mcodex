from __future__ import annotations

from pathlib import Path

import pytest

from mcodex.yaml_utils import safe_dump_yaml, safe_load_yaml


def test_safe_load_yaml_with_valid_dict(tmp_path: Path) -> None:
    """Test safe_load_yaml with valid dictionary YAML."""
    yaml_file = tmp_path / "test.yaml"
    yaml_file.write_text("key: value\nnumber: 42\n", encoding="utf-8")

    result = safe_load_yaml(yaml_file)

    assert result == {"key": "value", "number": 42}


def test_safe_load_yaml_with_empty_file(tmp_path: Path) -> None:
    """Test safe_load_yaml with empty file returns empty dict."""
    yaml_file = tmp_path / "empty.yaml"
    yaml_file.write_text("", encoding="utf-8")

    result = safe_load_yaml(yaml_file)

    assert result == {}


def test_safe_load_yaml_with_nested_dict(tmp_path: Path) -> None:
    """Test safe_load_yaml with nested dictionaries."""
    yaml_file = tmp_path / "nested.yaml"
    yaml_file.write_text("level1:\n  level2:\n    key: value\n", encoding="utf-8")

    result = safe_load_yaml(yaml_file)

    assert result == {"level1": {"level2": {"key": "value"}}}


def test_safe_load_yaml_with_list_at_root_raises_error(tmp_path: Path) -> None:
    """Test safe_load_yaml raises ValueError for list at root."""
    yaml_file = tmp_path / "list.yaml"
    yaml_file.write_text("- item1\n- item2\n", encoding="utf-8")

    with pytest.raises(ValueError) as exc_info:
        safe_load_yaml(yaml_file)

    assert "expected mapping" in str(exc_info.value).lower()
    assert "list" in str(exc_info.value).lower()


def test_safe_load_yaml_with_scalar_at_root_raises_error(tmp_path: Path) -> None:
    """Test safe_load_yaml raises ValueError for scalar at root."""
    yaml_file = tmp_path / "scalar.yaml"
    yaml_file.write_text("just a string\n", encoding="utf-8")

    with pytest.raises(ValueError) as exc_info:
        safe_load_yaml(yaml_file)

    assert "expected mapping" in str(exc_info.value).lower()


def test_safe_load_yaml_with_missing_file_raises_error(tmp_path: Path) -> None:
    """Test safe_load_yaml raises FileNotFoundError for missing file."""
    yaml_file = tmp_path / "nonexistent.yaml"

    with pytest.raises(FileNotFoundError):
        safe_load_yaml(yaml_file)


def test_safe_load_yaml_with_unicode(tmp_path: Path) -> None:
    """Test safe_load_yaml handles Unicode characters."""
    yaml_file = tmp_path / "unicode.yaml"
    yaml_file.write_text("title: Článek o něčem\nauthor: José\n", encoding="utf-8")

    result = safe_load_yaml(yaml_file)

    assert result == {"title": "Článek o něčem", "author": "José"}


def test_safe_dump_yaml_creates_valid_yaml(tmp_path: Path) -> None:
    """Test safe_dump_yaml creates valid YAML file."""
    yaml_file = tmp_path / "output.yaml"
    data = {"key": "value", "number": 42}

    safe_dump_yaml(data, yaml_file)

    assert yaml_file.exists()
    result = safe_load_yaml(yaml_file)
    assert result == data


def test_safe_dump_yaml_preserves_key_order(tmp_path: Path) -> None:
    """Test safe_dump_yaml preserves key order."""
    yaml_file = tmp_path / "ordered.yaml"
    data = {"z_key": "first", "a_key": "second", "m_key": "third"}

    safe_dump_yaml(data, yaml_file)

    content = yaml_file.read_text(encoding="utf-8")
    # Keys should appear in insertion order, not sorted
    z_pos = content.index("z_key")
    a_pos = content.index("a_key")
    m_pos = content.index("m_key")
    assert z_pos < a_pos < m_pos


def test_safe_dump_yaml_handles_unicode(tmp_path: Path) -> None:
    """Test safe_dump_yaml preserves Unicode characters."""
    yaml_file = tmp_path / "unicode_out.yaml"
    data = {"title": "Článek o něčem", "author": "José García"}

    safe_dump_yaml(data, yaml_file)

    content = yaml_file.read_text(encoding="utf-8")
    assert "Článek o něčem" in content
    assert "José García" in content


def test_safe_dump_yaml_with_nested_structures(tmp_path: Path) -> None:
    """Test safe_dump_yaml handles nested dictionaries and lists."""
    yaml_file = tmp_path / "nested.yaml"
    data = {
        "level1": {
            "level2": {"key": "value"},
            "list": ["item1", "item2"],
        }
    }

    safe_dump_yaml(data, yaml_file)

    result = safe_load_yaml(yaml_file)
    assert result == data


def test_roundtrip_dump_and_load(tmp_path: Path) -> None:
    """Test that dumping and loading preserves data."""
    yaml_file = tmp_path / "roundtrip.yaml"
    original = {
        "string": "value",
        "int": 42,
        "float": 3.14,
        "bool": True,
        "list": [1, 2, 3],
        "nested": {"a": 1, "b": 2},
    }

    safe_dump_yaml(original, yaml_file)
    result = safe_load_yaml(yaml_file)

    assert result == original


def test_safe_dump_yaml_overwrites_existing_file(tmp_path: Path) -> None:
    """Test safe_dump_yaml overwrites existing file."""
    yaml_file = tmp_path / "overwrite.yaml"
    yaml_file.write_text("old: data\n", encoding="utf-8")

    new_data = {"new": "data"}
    safe_dump_yaml(new_data, yaml_file)

    result = safe_load_yaml(yaml_file)
    assert result == new_data
    assert "old" not in result
