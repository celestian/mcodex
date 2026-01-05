from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from mcodex.services.pipeline import run_pipeline


def _write_min_text_dir(text_dir: Path) -> None:
    text_dir.mkdir(parents=True, exist_ok=True)
    (text_dir / "text.md").write_text("hello", encoding="utf-8")
    (text_dir / "metadata.yaml").write_text(
        yaml.safe_dump(
            {
                "metadata_version": 1,
                "id": "x",
                "title": "T",
                "slug": "story",
                "created_at": "2026-01-03T00:00:00+01:00",
                "authors": [],
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )


def test_run_pipeline_dry_run_collects_commands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tdir = tmp_path / "story"
    _write_min_text_dir(tdir)

    monkeypatch.setattr("shutil.which", lambda name: f"/bin/{name}")

    called: list[list[str]] = []

    def fake_run(cmd: list[str], cwd: Path) -> None:
        called.append(cmd)

    out = tmp_path / "out.pdf"
    result = run_pipeline(
        pipeline_name="pdf",
        source_dir=tdir,
        output_path=out,
        dry_run=True,
        run=fake_run,
    )

    assert result.output_path == out
    assert called == []
    assert len(result.commands) == 3
    assert result.commands[0][0].endswith("pandoc")
    assert result.commands[1][0].endswith("vlna")
    assert result.commands[2][0].endswith("latexmk")
