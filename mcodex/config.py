from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict
from pathlib import Path
from typing import Any

from mcodex.errors import PipelineConfigError, PipelineNotFoundError
from mcodex.models import Author
from mcodex.path_utils import normalize_path
from mcodex.yaml_utils import safe_dump_yaml, safe_load_yaml


class RepoConfigNotFoundError(FileNotFoundError):
    """Raised when no `.mcodex/config.yaml` can be found by walking upwards."""


DEFAULT_ARTIFACTS_DIR = "artifacts"
DEFAULT_SNAPSHOT_COMMIT_TEMPLATE = "Snapshot: {slug} / {label} — {note}"
DEFAULT_TEXT_PREFIX = "text_"


DEFAULT_PIPELINES: dict[str, Any] = {
    "pdf_pandoc": {
        "steps": [
            {"kind": "pandoc", "from": "markdown", "to": "pdf"},
        ],
    },
    "docx": {
        "steps": [
            {"kind": "pandoc", "from": "markdown", "to": "docx"},
        ],
    },
    "latex": {
        "steps": [
            {"kind": "pandoc", "from": "markdown", "to": "latex"},
        ],
    },
    "pdf": {
        "steps": [
            {
                "kind": "pandoc",
                "from": "markdown",
                "to": "latex",
                "output": "body_raw.tex",
            },
            {"kind": "vlna", "input": "body_raw.tex", "output": "body.tex"},
            {"kind": "latexmk", "engine": "lualatex", "main": "main.tex"},
        ],
    },
}


def repo_config_path(repo_root: Path) -> Path:
    return normalize_path(repo_root) / ".mcodex" / "config.yaml"


def find_repo_root(start: Path | None = None) -> Path:
    """Find repo root by searching for `.mcodex/config.yaml` upwards.

    Args:
        start: Directory (or file within a directory) to start searching from.

    Raises:
        RepoConfigNotFoundError: if no repo config anchor is found.
    """

    p = normalize_path(start or Path.cwd())
    if p.is_file():
        p = p.parent

    for candidate in [p, *p.parents]:
        if repo_config_path(candidate).exists():
            return candidate

    raise RepoConfigNotFoundError(
        "No .mcodex/config.yaml found. Run `mcodex init` in a Git repo first."
    )


def load_config(
    *,
    start: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = repo_root or find_repo_root(start)
    cfg_path = repo_config_path(root)
    if not cfg_path.exists():
        return {}
    return safe_load_yaml(cfg_path)


def save_config(
    config: dict[str, Any],
    *,
    repo_root: Path | None = None,
    start: Path | None = None,
) -> None:
    root = repo_root or find_repo_root(start)
    cfg_path = repo_config_path(root)
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    safe_dump_yaml(config, cfg_path)


def ensure_defaults(
    *,
    start: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Ensure required defaults exist in repo config.

    This is intentionally conservative: it only ensures keys needed by existing
    functionality (authors + snapshot commit template).
    """

    cfg = load_config(start=start, repo_root=repo_root)

    git = cfg.get("git")
    if git is None or not isinstance(git, dict):
        git = {}
        cfg["git"] = git

    commit_templates = git.get("commit_templates")
    if commit_templates is None or not isinstance(commit_templates, dict):
        commit_templates = {}
        git["commit_templates"] = commit_templates

    if "snapshot" not in commit_templates:
        commit_templates["snapshot"] = DEFAULT_SNAPSHOT_COMMIT_TEMPLATE
        save_config(cfg, start=start, repo_root=repo_root)

    return cfg


def get_pipelines(
    *,
    start: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    cfg = load_config(start=start, repo_root=repo_root)
    raw = cfg.get("pipelines")
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise PipelineConfigError("Invalid config: pipelines must be a mapping.")
    return raw


def validate_pipelines(pipelines: dict[str, Any]) -> None:
    if not isinstance(pipelines, dict) or not pipelines:
        raise PipelineConfigError(
            "Invalid config: pipelines must be a non-empty mapping."
        )

    for name, pipe in pipelines.items():
        if not isinstance(name, str) or not name.strip():
            raise PipelineConfigError(
                "Invalid config: pipeline names must be non-empty."
            )
        if not isinstance(pipe, dict):
            raise PipelineConfigError(
                f"Invalid config: pipeline '{name}' must be a mapping."
            )

        steps = pipe.get("steps")
        if not isinstance(steps, list) or not steps:
            raise PipelineConfigError(
                f"Invalid config: pipeline '{name}' must have non-empty steps."
            )

        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                raise PipelineConfigError(
                    f"Invalid config: pipeline '{name}' step {i} must be a mapping."
                )
            kind = step.get("kind")
            if not isinstance(kind, str) or not kind.strip():
                raise PipelineConfigError(
                    f"Invalid config: pipeline '{name}' step {i} missing kind."
                )
            if kind not in {"pandoc", "vlna", "latexmk"}:
                raise PipelineConfigError(
                    f"Invalid config: pipeline '{name}' step {i} unknown kind: {kind}"
                )

            if kind == "pandoc":
                _require_non_empty_str(step, "from", name, i)
                _require_non_empty_str(step, "to", name, i)
            if kind == "vlna":
                _require_non_empty_str(step, "input", name, i)
                _require_non_empty_str(step, "output", name, i)
            if kind == "latexmk":
                engine = step.get("engine")
                if engine is not None:
                    _require_non_empty_str(step, "engine", name, i)
                _require_non_empty_str(step, "main", name, i)


def _require_non_empty_str(
    step: dict[str, Any],
    field: str,
    pipeline_name: str,
    step_index: int,
) -> None:
    raw = step.get(field)
    if not isinstance(raw, str) or not raw.strip():
        raise PipelineConfigError(
            "Invalid config: "
            f"pipeline '{pipeline_name}' step {step_index} missing '{field}'."
        )


def get_pipeline(
    pipeline_name: str,
    *,
    start: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    pipelines = get_pipelines(start=start, repo_root=repo_root)
    validate_pipelines(pipelines)

    name = str(pipeline_name or "").strip()
    if not name:
        raise PipelineConfigError("Pipeline name cannot be empty.")

    pipe = pipelines.get(name)
    if pipe is None:
        available = tuple(sorted(str(n) for n in pipelines.keys()))
        raise PipelineNotFoundError(requested=name, available=available)
    if not isinstance(pipe, dict):
        raise PipelineConfigError(f"Invalid pipeline config for '{name}'.")
    return pipe


def get_snapshot_commit_template(
    *,
    start: Path | None = None,
    repo_root: Path | None = None,
) -> str:
    cfg = ensure_defaults(start=start, repo_root=repo_root)
    git = cfg.get("git", {})
    commit_templates = git.get("commit_templates", {})
    tpl = commit_templates.get("snapshot")
    if not isinstance(tpl, str) or not tpl.strip():
        return DEFAULT_SNAPSHOT_COMMIT_TEMPLATE
    return tpl.strip()


def load_authors(
    *,
    start: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Author]:
    cfg = load_config(start=start, repo_root=repo_root)
    raw_authors = cfg.get("authors", [])
    out: dict[str, Author] = {}

    if not isinstance(raw_authors, list):
        return out

    for a in raw_authors:
        if not isinstance(a, dict):
            continue
        nickname = str(a.get("nickname", "")).strip()
        first_name = str(a.get("first_name", "")).strip()
        last_name = str(a.get("last_name", "")).strip()
        email = str(a.get("email", "")).strip()

        if not nickname or not first_name or not last_name or not email:
            continue

        out[nickname] = Author(
            nickname=nickname,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )

    return out


def get_text_prefix(
    *,
    start: Path | None = None,
    repo_root: Path | None = None,
) -> str:
    cfg = load_config(start=start, repo_root=repo_root)
    raw = cfg.get("text_prefix")
    if not isinstance(raw, str):
        return DEFAULT_TEXT_PREFIX
    value = raw.strip()
    if not value:
        return DEFAULT_TEXT_PREFIX
    return value


def get_artifacts_dir(
    *,
    start: Path | None = None,
    repo_root: Path | None = None,
) -> str:
    cfg = load_config(start=start, repo_root=repo_root)
    raw = cfg.get("artifacts_dir")
    if not isinstance(raw, str):
        return DEFAULT_ARTIFACTS_DIR

    value = raw.strip().strip("/")
    if not value:
        return DEFAULT_ARTIFACTS_DIR

    if "/" in value or "\\" in value:
        raise ValueError(
            "Invalid artifacts_dir: must be a single directory name (no slashes)."
        )

    return value


def resolve_artifacts_path(
    *,
    start: Path | None = None,
    repo_root: Path | None = None,
) -> Path:
    root = repo_root or find_repo_root(start)
    return root / get_artifacts_dir(repo_root=root)


def save_authors(
    authors: dict[str, Author],
    *,
    start: Path | None = None,
    repo_root: Path | None = None,
) -> None:
    cfg = load_config(start=start, repo_root=repo_root)
    cfg["authors"] = [asdict(a) for a in authors.values()]
    save_config(cfg, start=start, repo_root=repo_root)


def is_under_repo(start: Path | None = None) -> bool:
    try:
        find_repo_root(start)
    except RepoConfigNotFoundError:
        return False
    return True


def validate_allowed_roots(roots: Iterable[Path]) -> list[Path]:
    """Normalize allowed roots used in safety-critical operations."""

    out: list[Path] = []
    for r in roots:
        out.append(normalize_path(r))
    return out
