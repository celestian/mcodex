from __future__ import annotations

from pathlib import Path

import pytest

from mcodex.config import RepoConfigNotFoundError, find_repo_root, repo_config_path
from mcodex.services.init_repo import init_repo


def test_find_repo_root_walks_up(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    cfg_dir = repo / ".mcodex"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "config.yaml").write_text("{}\n", encoding="utf-8")

    nested = repo / "a" / "b" / "c"
    nested.mkdir(parents=True)

    assert find_repo_root(nested) == repo
    assert repo_config_path(repo) == cfg_dir / "config.yaml"


def test_find_repo_root_raises_when_missing(tmp_path: Path) -> None:
    with pytest.raises(RepoConfigNotFoundError):
        find_repo_root(tmp_path)


def test_init_repo_creates_config_templates_and_gitignore(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()

    init_repo(repo)

    assert (repo / ".mcodex" / "config.yaml").exists()
    assert (repo / ".mcodex" / "templates").exists()

    gi = (repo / ".gitignore").read_text(encoding="utf-8")
    assert "artifacts/" in gi

    init_repo(repo)
    gi2 = (repo / ".gitignore").read_text(encoding="utf-8")
    assert gi2.count("artifacts/") == 1
