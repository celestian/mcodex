from __future__ import annotations

import subprocess
from pathlib import Path

from behave import given, then

from mcodex.services.fs import TEST_ROOT_MARKER, safe_rmtree


@given("I remove git repository")
def step_remove_git_repo(context) -> None:
    git_dir = Path(context.workdir) / ".git"
    if git_dir.exists():
        safe_rmtree(git_dir, marker_name=TEST_ROOT_MARKER)


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
