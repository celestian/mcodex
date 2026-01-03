from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from behave import given, then


@given("I remove git repository")
def step_remove_git_repo(context) -> None:
    git_dir = Path(context.workdir) / ".git"
    if git_dir.exists():
        shutil.rmtree(git_dir)


@then('git tag "{tag}" exists')
def step_git_tag_exists(context, tag: str) -> None:
    completed = subprocess.run(
        ["git", "-C", str(context.workdir), "tag", "-l", tag],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(
            "Git tag listing failed:\n"
            f"  rc: {completed.returncode}\n"
            f"  out: {completed.stdout}\n"
            f"  err: {completed.stderr}\n"
        )
    assert completed.stdout.strip() == tag, completed.stdout
