from __future__ import annotations

from pathlib import Path

from mcodex.services.pipeline_list import pipeline_list


def test_pipeline_list_prints_names_and_steps(tmp_path: Path, capsys: object) -> None:
    repo = tmp_path / "repo"
    (repo / ".mcodex").mkdir(parents=True)
    (repo / ".mcodex" / "config.yaml").write_text(
        "pipelines:\n"
        "  pdf:\n"
        "    steps:\n"
        "      - kind: pandoc\n"
        "        from: markdown\n"
        "        to: latex\n"
        "        output: body_raw.tex\n"
        "      - kind: vlna\n"
        "        input: body_raw.tex\n"
        "        output: body.tex\n"
        "      - kind: latexmk\n"
        "        engine: lualatex\n"
        "        main: main.tex\n"
        "  docx:\n"
        "    steps:\n"
        "      - kind: pandoc\n"
        "        from: markdown\n"
        "        to: docx\n",
        encoding="utf-8",
    )

    pipeline_list(start=repo)

    out = capsys.readouterr().out
    assert "pdf" in out
    assert "(default)" in out
    assert "docx" in out
    assert "pandoc markdown -> latex" in out
    assert "vlna body_raw.tex -> body.tex" in out
    assert "latexmk engine=lualatex main=main.tex" in out
