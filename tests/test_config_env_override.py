from __future__ import annotations

from pathlib import Path

import pytest

from mcodex.config import default_config_path


def test_default_config_path_uses_env_override(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    override = tmp_path / "custom-config.yaml"
    monkeypatch.setenv("MCODEX_CONFIG_PATH", str(override))

    assert default_config_path() == override


def test_default_config_path_expands_user(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCODEX_CONFIG_PATH", "~/mcodex-config.yaml")

    assert str(default_config_path()).endswith("/mcodex-config.yaml")
    assert default_config_path().is_absolute()
