from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

import yaml
from behave import given, then, when


def _normalize_command(command: str) -> str:
    return command.replace('\\"', '"').replace("\\'", "'")


@given("an empty mcodex config")
def step_empty_config(context) -> None:
    context.cfg_path.parent.mkdir(parents=True, exist_ok=True)
    if context.cfg_path.exists():
        context.cfg_path.unlink()


@when('I run "{command}"')
def step_run_command(context, command: str) -> None:
    command = _normalize_command(command)
    args = shlex.split(command)

    completed = subprocess.run(
        args,
        cwd=context.workdir,
        text=True,
        capture_output=True,
        check=False,
    )
    context.last = completed

    if completed.returncode != 0:
        raise AssertionError(
            "Command failed:\n"
            f"  cmd: {command}\n"
            f"  rc: {completed.returncode}\n"
            f"  out: {completed.stdout}\n"
            f"  err: {completed.stderr}\n"
        )


@then('a text directory "{slug}" exists')
def step_text_dir_exists(context, slug: str) -> None:
    p = Path(context.workdir) / slug
    assert p.exists() and p.is_dir(), f"Missing directory: {p}"


def _load_metadata(context, slug: str) -> dict:
    meta_path = Path(context.workdir) / slug / "metadata.yaml"
    assert meta_path.exists(), f"Missing metadata: {meta_path}"
    return yaml.safe_load(meta_path.read_text(encoding="utf-8"))


@then('the metadata in "{slug}" contains author "{nickname}"')
def step_metadata_contains_author(context, slug: str, nickname: str) -> None:
    data = _load_metadata(context, slug)

    assert data.get("metadata_version") == 1
    authors = data.get("authors", [])
    assert isinstance(authors, list)

    found = any(isinstance(a, dict) and a.get("nickname") == nickname for a in authors)
    assert found, f"Author {nickname} not found in metadata authors."


@then('the metadata in "{slug}" does not contain author "{nickname}"')
def step_metadata_not_contains_author(context, slug: str, nickname: str) -> None:
    data = _load_metadata(context, slug)

    assert data.get("metadata_version") == 1
    authors = data.get("authors", [])
    assert isinstance(authors, list)

    found = any(isinstance(a, dict) and a.get("nickname") == nickname for a in authors)
    assert not found, f"Author {nickname} unexpectedly present in metadata authors."


@then('running "{command}" fails with "{message}"')
def step_run_fails_with(context, command: str, message: str) -> None:
    command = _normalize_command(command)
    args = shlex.split(command)

    completed = subprocess.run(
        args,
        cwd=context.workdir,
        text=True,
        capture_output=True,
        check=False,
    )
    context.last = completed

    assert completed.returncode != 0, (
        "Expected command to fail but it succeeded:\n"
        f"  cmd: {command}\n"
        f"  out: {completed.stdout}\n"
        f"  err: {completed.stderr}\n"
    )
    combined = (completed.stdout or "") + (completed.stderr or "")
    assert message in combined, combined
