from __future__ import annotations

from pathlib import Path

from behave import then, when


@when('I cd into "{slug}"')
def step_cd_into(context, slug: str) -> None:
    context.workdir = Path(context.workdir) / slug
    if not context.workdir.exists():
        raise AssertionError(f"Missing directory: {context.workdir}")


@when('I cd to external directory "{name}"')
def step_cd_external(context, name: str) -> None:
    test_root = Path(context.test_root)
    external = test_root / name
    external.mkdir(parents=True, exist_ok=True)
    context.workdir = external


@then('snapshot "{label}" exists')
def step_snapshot_exists(context, label: str) -> None:
    p = Path(context.workdir) / ".snapshot" / label
    assert p.exists() and p.is_dir(), f"Missing snapshot directory: {p}"


@then('status shows current stage "{stage}"')
def step_status_shows_stage(context, stage: str) -> None:
    from subprocess import run

    completed = run(
        ["mcodex", "status"],
        cwd=context.workdir,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(
            "Command failed:\n"
            f"  rc: {completed.returncode}\n"
            f"  out: {completed.stdout}\n"
            f"  err: {completed.stderr}\n"
        )

    out = completed.stdout
    assert f"Current stage: {stage}" in out, out
