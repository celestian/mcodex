from __future__ import annotations

from pathlib import Path

from mcodex import version as version_module


def test_get_version_uses_importlib_metadata(monkeypatch) -> None:
    def fake_version(dist_name: str) -> str:
        assert dist_name == "mcodex"
        return "1.2.3"

    monkeypatch.setattr(version_module.importlib_metadata, "version", fake_version)

    assert version_module.get_version() == "1.2.3"


def test_get_version_falls_back_to_pyproject(monkeypatch, tmp_path: Path) -> None:
    def fake_version(_: str) -> str:
        raise version_module.importlib_metadata.PackageNotFoundError

    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(
        """
        [project]
        name = "mcodex"
        version = "9.9.9"
        """.strip()
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(version_module.importlib_metadata, "version", fake_version)
    monkeypatch.setattr(version_module, "_get_pyproject_path", lambda: pyproject_path)

    assert version_module.get_version() == "9.9.9"
