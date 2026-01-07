from __future__ import annotations

from importlib import metadata as importlib_metadata
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


def _get_pyproject_path() -> Path:
    return Path(__file__).resolve().parents[1] / "pyproject.toml"


def _read_version_from_pyproject(pyproject_path: Path) -> str | None:
    try:
        raw = pyproject_path.read_bytes()
    except FileNotFoundError:
        return None

    try:
        data = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        return None

    project = data.get("project")
    if not isinstance(project, dict):
        return None

    version = project.get("version")
    if not isinstance(version, str):
        return None
    if not version.strip():
        return None
    return version.strip()


def get_version() -> str:
    """Return the installed distribution version.

    Order:
      1) importlib.metadata.version("mcodex")
      2) Read version from pyproject.toml in the working tree (dev fallback)
      3) "0.0.0"
    """

    try:
        return importlib_metadata.version("mcodex")
    except importlib_metadata.PackageNotFoundError:
        pass

    version = _read_version_from_pyproject(_get_pyproject_path())
    if version is not None:
        return version

    return "0.0.0"

