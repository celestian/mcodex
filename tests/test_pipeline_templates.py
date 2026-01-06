from __future__ import annotations

from pathlib import Path

import yaml

from mcodex.services import pipeline as pipeline_mod


def _write_repo_config(repo_root: Path, pipelines: dict) -> None:
    cfg_path = repo_root / ".mcodex" / "config.yaml"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(
        yaml.safe_dump({"pipelines": pipelines}, sort_keys=False),
        encoding="utf-8",
    )


def _write_text_source(source_dir: Path) -> None:
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "text.md").write_text("# Title\n", encoding="utf-8")


def test_pandoc_docx_uses_repo_reference_doc(monkeypatch, tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    text_dir = repo_root / "text_demo"

    _write_repo_config(
        repo_root,
        pipelines={
            "docx": {
                "steps": [
                    {"kind": "pandoc", "from": "markdown", "to": "docx"},
                ]
            }
        },
    )
    _write_text_source(text_dir)

    ref = repo_root / ".mcodex" / "templates" / "pandoc" / "reference.docx"
    ref.parent.mkdir(parents=True, exist_ok=True)
    ref.write_bytes(b"fake-docx")

    monkeypatch.setattr(pipeline_mod, "_require_executable", lambda name: name)

    out = repo_root / "artifacts" / "out.docx"
    result = pipeline_mod.run_pipeline(
        pipeline_name="docx",
        source_dir=text_dir,
        output_path=out,
        dry_run=True,
    )

    cmd = result.commands[0]
    assert any(arg.startswith("--reference-doc=") for arg in cmd)
    assert f"--reference-doc={ref}" in cmd


def test_pandoc_pdf_uses_repo_template_tex(monkeypatch, tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    text_dir = repo_root / "text_demo"

    _write_repo_config(
        repo_root,
        pipelines={
            "pdf_pandoc": {
                "steps": [
                    {"kind": "pandoc", "from": "markdown", "to": "pdf"},
                ]
            }
        },
    )
    _write_text_source(text_dir)

    tex = repo_root / ".mcodex" / "templates" / "pandoc" / "template.tex"
    tex.parent.mkdir(parents=True, exist_ok=True)
    tex.write_text("% fake template\n", encoding="utf-8")

    monkeypatch.setattr(pipeline_mod, "_require_executable", lambda name: name)

    out = repo_root / "artifacts" / "out.pdf"
    result = pipeline_mod.run_pipeline(
        pipeline_name="pdf_pandoc",
        source_dir=text_dir,
        output_path=out,
        dry_run=True,
    )

    cmd = result.commands[0]
    assert any(arg.startswith("--template=") for arg in cmd)
    assert f"--template={tex}" in cmd


def test_pandoc_does_not_add_template_args_when_files_missing(
    monkeypatch, tmp_path: Path
) -> None:
    repo_root = tmp_path / "repo"
    text_dir = repo_root / "text_demo"

    _write_repo_config(
        repo_root,
        pipelines={
            "docx": {
                "steps": [
                    {"kind": "pandoc", "from": "markdown", "to": "docx"},
                ]
            }
        },
    )
    _write_text_source(text_dir)

    monkeypatch.setattr(pipeline_mod, "_require_executable", lambda name: name)

    out = repo_root / "artifacts" / "out.docx"
    result = pipeline_mod.run_pipeline(
        pipeline_name="docx",
        source_dir=text_dir,
        output_path=out,
        dry_run=True,
    )

    cmd = result.commands[0]
    assert not any(arg.startswith("--reference-doc=") for arg in cmd)
    assert not any(arg.startswith("--template=") for arg in cmd)
