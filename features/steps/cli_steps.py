from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

import yaml
from behave import given, then, when


def _expand_placeholders(context, value: str) -> str:
    repo_root = str(getattr(context, "repo_root", ""))
    workdir = str(getattr(context, "workdir", ""))
    return value.replace("{REPO_ROOT}", repo_root).replace("{WORKDIR}", workdir)


def _normalize_command(context, command: str) -> str:
    unescaped = command.replace('\\"', '"').replace("\\'", "'")
    return _expand_placeholders(context, unescaped)


@given("an empty mcodex config")
def step_empty_config(context) -> None:
    cfg_dir = Path(context.workdir) / ".mcodex"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg_path = cfg_dir / "config.yaml"
    cfg_path.write_text("{}\n", encoding="utf-8")

    templates_dir = cfg_dir / "templates" / "text"
    templates_dir.mkdir(parents=True, exist_ok=True)
    (templates_dir / "todo.md").write_text("# TODO\n", encoding="utf-8")
    (templates_dir / "checklist.md").write_text(
        "# Checklist\n",
        encoding="utf-8",
    )


@when('I run "{command}"')
def step_run_command(context, command: str) -> None:
    command = _normalize_command(context, command)
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


@then('a file "{relpath}" exists')
def step_file_exists(context, relpath: str) -> None:
    relpath = _expand_placeholders(context, relpath)
    p = Path(context.workdir) / relpath
    assert p.exists() and p.is_file(), f"Missing file: {p}"


@then('a directory "{relpath}" exists')
def step_dir_exists(context, relpath: str) -> None:
    relpath = _expand_placeholders(context, relpath)
    p = Path(context.workdir) / relpath
    assert p.exists() and p.is_dir(), f"Missing directory: {p}"


@then('the file "{relpath}" contains "{text}"')
def step_file_contains(context, relpath: str, text: str) -> None:
    relpath = _expand_placeholders(context, relpath)
    p = Path(context.workdir) / relpath
    assert p.exists() and p.is_file(), f"Missing file: {p}"
    data = p.read_text(encoding="utf-8")
    assert text in data, data


def _load_metadata(context, slug: str) -> dict:
    meta_path = Path(context.workdir) / slug / "metadata.yaml"
    assert meta_path.exists(), f"Missing metadata: {meta_path}"
    return yaml.safe_load(meta_path.read_text(encoding="utf-8"))


@then('the metadata in "{slug}" contains author "{nickname}"')
def step_metadata_contains_author(context, slug: str, nickname: str) -> None:
    slug = _expand_placeholders(context, slug)
    data = _load_metadata(context, slug)

    assert data.get("metadata_version") == 1
    authors = data.get("authors", [])
    assert isinstance(authors, list)

    found = any(isinstance(a, dict) and a.get("nickname") == nickname for a in authors)
    assert found, f"Author {nickname} not found in metadata authors."


@then('the metadata in "{slug}" does not contain author "{nickname}"')
def step_metadata_not_contains_author(context, slug: str, nickname: str) -> None:
    slug = _expand_placeholders(context, slug)
    data = _load_metadata(context, slug)

    assert data.get("metadata_version") == 1
    authors = data.get("authors", [])
    assert isinstance(authors, list)

    found = any(isinstance(a, dict) and a.get("nickname") == nickname for a in authors)
    assert not found, f"Author {nickname} unexpectedly present in metadata authors."


@then('running "{command}" fails with "{message}"')
def step_run_fails_with(context, command: str, message: str) -> None:
    command = _normalize_command(context, command)
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
