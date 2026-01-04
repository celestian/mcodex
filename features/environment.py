from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from mcodex.services.fs import TEST_ROOT_MARKER, ensure_test_root_marker, safe_rmtree


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def before_scenario(context, scenario) -> None:
    # Stable root for the whole scenario; this is what we delete afterwards.
    context.test_root = Path(tempfile.mkdtemp(prefix="mcodex_behave_")).resolve()
    ensure_test_root_marker(context.test_root)

    # The actual git repo lives inside test_root/repo so we can also create
    # "outside repo" directories as siblings within test_root.
    context.repo_root = context.test_root / "repo"
    context.repo_root.mkdir(parents=True, exist_ok=True)

    try:
        _git("init", "-b", "main", cwd=context.repo_root)
    except subprocess.CalledProcessError:
        _git("init", cwd=context.repo_root)
        _git("checkout", "-b", "main", cwd=context.repo_root)

    _git("config", "user.name", "Behave", cwd=context.repo_root)
    _git("config", "user.email", "behave@example.invalid", cwd=context.repo_root)

    (context.repo_root / ".gitignore").write_text("", encoding="utf-8")
    _git("add", ".gitignore", cwd=context.repo_root)
    _git("commit", "-m", "init", cwd=context.repo_root)

    # Current working directory for steps
    context.workdir = context.repo_root


def after_scenario(context, scenario) -> None:
    test_root = getattr(context, "test_root", None)
    if test_root is None:
        return

    safe_rmtree(Path(test_root), marker_name=TEST_ROOT_MARKER, ignore_errors=True)
