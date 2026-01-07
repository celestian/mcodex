from __future__ import annotations

from pathlib import Path

import yaml

from mcodex.services.build_context import write_build_context


def _write_metadata(path: Path) -> None:
    path.write_text(
        yaml.safe_dump(
            {
                "metadata_version": 1,
                "id": "x",
                "title": "My Title",
                "slug": "story",
                "created_at": "2026-01-03T00:00:00+01:00",
                "authors": [
                    {"nickname": "alice"},
                    {"nickname": "bob"},
                ],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )


def test_build_context_worktree_has_metadata_and_runtime(tmp_path: Path) -> None:
    src = tmp_path / "text"
    src.mkdir(parents=True, exist_ok=True)
    _write_metadata(src / "metadata.yaml")

    tmp = tmp_path / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)

    result = write_build_context(
        tmp_dir=tmp,
        source_dir=src,
        pipeline_name="pdf",
        version_label="worktree",
    )

    assert result.yaml_path.exists()
    ctx = yaml.safe_load(result.yaml_path.read_text(encoding="utf-8"))
    assert ctx["title"] == "My Title"
    assert ctx["author"] == ["alice", "bob"]
    assert ctx["build"]["pipeline"] == "pdf"
    assert ctx["build"]["version"] == "worktree"
    assert "built_at" in ctx["build"]
    assert "snapshot" not in ctx


def test_build_context_snapshot_merges_snapshot_yaml(tmp_path: Path) -> None:
    src = tmp_path / "text" / ".snapshot" / "draft-1"
    src.mkdir(parents=True, exist_ok=True)
    _write_metadata(src / "metadata.yaml")
    (src / "snapshot.yaml").write_text(
        yaml.safe_dump(
            {
                "label": "draft-1",
                "created_at": "2026-01-04T00:00:00+01:00",
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )

    tmp = tmp_path / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)

    result = write_build_context(
        tmp_dir=tmp,
        source_dir=src,
        pipeline_name="pdf",
        version_label="draft-1",
    )

    ctx = yaml.safe_load(result.yaml_path.read_text(encoding="utf-8"))
    assert ctx["snapshot"]["label"] == "draft-1"
    assert ctx["snapshot_label"] == "draft-1"
