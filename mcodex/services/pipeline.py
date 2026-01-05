from __future__ import annotations

import shutil
import subprocess
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from mcodex.config import (
    DEFAULT_PIPELINES,
    RepoConfigNotFoundError,
    find_repo_root,
    get_pipeline,
    validate_pipelines,
)


@dataclass(frozen=True)
class PipelineResult:
    output_path: Path
    commands: list[list[str]]


RunFn = Callable[[list[str], Path], None]


def _require_executable(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise RuntimeError(
            f"Required executable not found: {name}. "
            "Install it and ensure it is on PATH."
        )
    return path


def _default_run(cmd: list[str], cwd: Path) -> None:
    completed = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode == 0:
        return

    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()

    parts: list[str] = [f"Command failed: {' '.join(cmd)}"]
    if stdout:
        parts.append("--- stdout ---")
        parts.append(stdout)
    if stderr:
        parts.append("--- stderr ---")
        parts.append(stderr)
    if not stdout and not stderr:
        parts.append("(no output)")

    raise RuntimeError("\n".join(parts))


def run_pipeline(
    *,
    pipeline_name: str,
    source_dir: Path,
    output_path: Path,
    dry_run: bool = False,
    run: RunFn | None = None,
) -> PipelineResult:
    """Execute a configured pipeline.

    The pipeline is taken from `.mcodex/config.yaml` if `source_dir` is in a
    mcodex repo; otherwise `DEFAULT_PIPELINES` are used.
    """

    source_dir = source_dir.expanduser().resolve()
    output_path = output_path.expanduser().resolve()

    commands: list[list[str]] = []
    runner = run or _default_run

    try:
        repo_root = find_repo_root(source_dir)
        pipe = get_pipeline(pipeline_name, repo_root=repo_root)
    except RepoConfigNotFoundError:
        validate_pipelines(DEFAULT_PIPELINES)
        pipe = DEFAULT_PIPELINES[pipeline_name]

    steps = pipe["steps"]
    validate_pipelines({pipeline_name: pipe})

    src_md = source_dir / "text.md"
    if not src_md.exists():
        raise FileNotFoundError(f"Source text not found: {src_md}")

    with tempfile.TemporaryDirectory(prefix="mcodex-build-") as td:
        tmp = Path(td)

        env: dict[str, Path] = {
            "source": src_md,
        }

        for step in steps:
            kind = str(step["kind"]).strip()

            if kind == "pandoc":
                pandoc = _require_executable("pandoc")
                to = str(step["to"]).strip()
                from_ = str(step["from"]).strip()

                if to in {"pdf", "docx"}:
                    out = output_path
                else:
                    out_name = str(step.get("output") or "body_raw.tex")
                    out = tmp / out_name

                cmd = [
                    pandoc,
                    str(env["source"]),
                    f"--from={from_}",
                    f"--to={to}",
                    "-o",
                    str(out),
                ]
                commands.append(cmd)
                if not dry_run:
                    runner(cmd, source_dir)
                env["pandoc_out"] = out
                continue

            if kind == "vlna":
                vlna = _require_executable("vlna")
                inp = tmp / str(step["input"]).strip()
                out = tmp / str(step["output"]).strip()
                cmd = [
                    vlna,
                    "-f",
                    "-l",
                    "-m",
                    "-n",
                    str(inp),
                    str(out),
                ]
                commands.append(cmd)
                if not dry_run:
                    runner(cmd, tmp)
                env["vlna_out"] = out
                continue

            if kind == "latexmk":
                latexmk = _require_executable("latexmk")
                engine = str(step.get("engine") or "lualatex").strip()
                main_name = str(step["main"]).strip()
                main = tmp / main_name

                body = env.get("vlna_out") or env.get("pandoc_out")
                if not isinstance(body, Path):
                    raise RuntimeError(
                        "latexmk step requires prior pandoc output (and vlna "
                        "output, if configured)."
                    )

                if not dry_run:
                    if not body.exists():
                        raise RuntimeError(
                            f"latexmk step missing prior output file: {body}"
                        )

                    # Prefer repo template if available; fall back to a minimal one.
                    template = _try_find_repo_template(source_dir)
                    if template is not None:
                        main.write_text(
                            template.read_text(encoding="utf-8"),
                            encoding="utf-8",
                        )
                    else:
                        main.write_text(
                            _fallback_latex_template(),
                            encoding="utf-8",
                        )

                    (tmp / "body.tex").write_text(
                        body.read_text(encoding="utf-8"),
                        encoding="utf-8",
                    )

                cmd = [
                    latexmk,
                    "-pdf",
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-file-line-error",
                    "-e",
                    f"$pdflatex=q/{engine} %O %S/;",
                    str(main.name),
                ]
                commands.append(cmd)
                if not dry_run:
                    runner(cmd, tmp)

                built_pdf = tmp / "main.pdf"
                if not dry_run and not built_pdf.exists():
                    raise RuntimeError("latexmk finished without producing main.pdf")

                if not dry_run:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(built_pdf, output_path)
                continue

            raise AssertionError(f"Unexpected step kind: {kind}")

        if steps and str(steps[-1]["kind"]).strip() == "pandoc":
            if not dry_run:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(env["pandoc_out"], output_path)

    return PipelineResult(output_path=output_path, commands=commands)


def _try_find_repo_template(source_dir: Path) -> Path | None:
    try:
        repo_root = find_repo_root(source_dir)
    except RepoConfigNotFoundError:
        return None

    candidate = repo_root / ".mcodex" / "templates" / "latex" / "main.tex"
    if candidate.exists() and candidate.is_file():
        return candidate
    return None


def _fallback_latex_template() -> str:
    return """\\documentclass[12pt]{article}

\\usepackage[a4paper,margin=25mm]{geometry}
\\usepackage{fontspec}
\\usepackage{microtype}
\\usepackage{setspace}
\\usepackage{parskip}
\\usepackage{hyperref}

\\providecommand{\\tightlist}{}

\\setstretch{1.15}

\\begin{document}
\\input{body.tex}
\\end{document}
"""
