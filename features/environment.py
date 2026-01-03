from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


def _ensure_base_dir(context) -> None:
    # Behave normally provides this; make it explicit and robust.
    cfg = getattr(context, "config", None)
    if cfg is not None and getattr(cfg, "base_dir", None):
        context.base_dir = Path(cfg.base_dir)
    else:
        # Fallback: assume current working directory contains "features".
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

    # Workspace outside the project repo to avoid git discovery climbing up.
    context.workdir = Path(tempfile.mkdtemp(prefix="mcodex_behave_"))

    context.cfg_path = context.workdir / "config.yaml"
    os.environ["MCODEX_CONFIG_PATH"] = str(context.cfg_path)

    # Git identity for commits made by mcodex snapshot code.
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
    if workdir is not None:
        shutil.rmtree(str(workdir), ignore_errors=True)
