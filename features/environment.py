from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

from mcodex.services.fs import TEST_ROOT_MARKER, ensure_test_root_marker, safe_rmtree


def _ensure_base_dir(context) -> None:
    cfg = getattr(context, "config", None)
    if cfg is not None and getattr(cfg, "base_dir", None):
        context.base_dir = Path(cfg.base_dir)
        return

    context.base_dir = Path.cwd() / "features"


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


def before_scenario(context, scenario) -> None:
    _ensure_base_dir(context)

    context.workdir = Path(tempfile.mkdtemp(prefix="mcodex_behave_"))
    ensure_test_root_marker(context.workdir)

    context.cfg_path = context.workdir / "config.yaml"
    os.environ["MCODEX_CONFIG_PATH"] = str(context.cfg_path)

    os.environ["GIT_AUTHOR_NAME"] = "Behave"
    os.environ["GIT_AUTHOR_EMAIL"] = "behave@example.invalid"
    os.environ["GIT_COMMITTER_NAME"] = "Behave"
    os.environ["GIT_COMMITTER_EMAIL"] = "behave@example.invalid"

    try:
        _git("init", "-b", "main", cwd=context.workdir)
    except subprocess.CalledProcessError:
        _git("init", cwd=context.workdir)
        _git("checkout", "-b", "main", cwd=context.workdir)

    _git("config", "user.name", "Behave", cwd=context.workdir)
    _git("config", "user.email", "behave@example.invalid", cwd=context.workdir)

    (context.workdir / ".gitignore").write_text("", encoding="utf-8")
    _git("add", ".gitignore", cwd=context.workdir)
    _git("commit", "-m", "init", cwd=context.workdir)


def after_scenario(context, scenario) -> None:
    os.environ.pop("MCODEX_CONFIG_PATH", None)
    os.environ.pop("GIT_AUTHOR_NAME", None)
    os.environ.pop("GIT_AUTHOR_EMAIL", None)
    os.environ.pop("GIT_COMMITTER_NAME", None)
    os.environ.pop("GIT_COMMITTER_EMAIL", None)

    workdir = getattr(context, "workdir", None)
    if workdir is None:
        return

    safe_rmtree(Path(workdir), marker_name=TEST_ROOT_MARKER, ignore_errors=True)
