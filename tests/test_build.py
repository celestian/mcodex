from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

from mcodex.services.build import build_pdf


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


def test_build_pdf_worktree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tdir = tmp_path / "story"
    _write_min_text_dir(tdir)

    monkeypatch.setattr("shutil.which", lambda name: f"/bin/{name}")

    def fake_run(
        cmd: list[str],
        cwd: str | None = None,
        text: bool | None = None,
        capture_output: bool | None = None,
        check: bool | None = None,
        **kwargs: Any,
    ) -> subprocess.CompletedProcess[str]:
        _ = text, capture_output, check
        cwd_path = Path(cwd or ".")

        if cmd and cmd[0].endswith("pandoc"):
            out = Path(cmd[cmd.index("-o") + 1])
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text("body", encoding="utf-8")

        if cmd and cmd[0].endswith("vlna"):
            out = Path(cmd[-1])
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text("vlna", encoding="utf-8")

        if cmd and cmd[0].endswith("latexmk"):
            (cwd_path / "main.pdf").write_text("%PDF", encoding="utf-8")

        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)

    out = build_pdf(text_dir=tdir, version=".")

    assert out.exists()
    assert out.name == "story_worktree.pdf"
    assert out.parent.name == "artifacts"
    assert out.parent.parent == tmp_path


def test_build_pdf_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tdir = tmp_path / "story"
    _write_min_text_dir(tdir)

    snap = tdir / ".snapshot" / "draft-1"
    snap.mkdir(parents=True)
    (snap / "text.md").write_text("snap", encoding="utf-8")
    (snap / "metadata.yaml").write_text(
        (tdir / "metadata.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    monkeypatch.setattr("shutil.which", lambda name: f"/bin/{name}")

    def fake_run(
        cmd: list[str],
        cwd: str | None = None,
        text: bool | None = None,
        capture_output: bool | None = None,
        check: bool | None = None,
        **kwargs: Any,
    ) -> subprocess.CompletedProcess[str]:
        _ = text, capture_output, check
        cwd_path = Path(cwd or ".")

        if cmd and cmd[0].endswith("pandoc"):
            out = Path(cmd[cmd.index("-o") + 1])
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text("body", encoding="utf-8")

        if cmd and cmd[0].endswith("vlna"):
            out = Path(cmd[-1])
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text("vlna", encoding="utf-8")

        if cmd and cmd[0].endswith("latexmk"):
            (cwd_path / "main.pdf").write_text("%PDF", encoding="utf-8")

        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)

    out = build_pdf(text_dir=tdir, version="draft-1")

    assert out.exists()
    assert out.name == "story_draft-1.pdf"
    assert out.parent.name == "artifacts"
    assert out.parent.parent == tmp_path
