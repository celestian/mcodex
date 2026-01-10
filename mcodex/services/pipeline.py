from __future__ import annotations

import importlib.resources
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path

from mcodex.config import (
    DEFAULT_PIPELINES,
    find_repo_root,
    get_pipeline,
    validate_pipelines,
)
from mcodex.errors import BuildToolError, RepoConfigNotFoundError
from mcodex.services.build_context import write_build_context


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
        timeout=300,  # 5 minutes
    )
    if completed.returncode == 0:
        return

    tool = cmd[0] if cmd else "unknown"
    output = "\n".join(filter(None, [completed.stdout, completed.stderr]))
    raise BuildToolError(tool, completed.returncode, output)


def _copy_dir_contents(src_dir: Path, dst_dir: Path) -> None:
    if not src_dir.exists() or not src_dir.is_dir():
        raise FileNotFoundError(f"Template directory not found: {src_dir}")

    for item in src_dir.rglob("*"):
        rel = item.relative_to(src_dir)
        target = dst_dir / rel

        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(item, target)


def _repo_templates_root(source_dir: Path) -> Path | None:
    try:
        repo_root = find_repo_root(source_dir)
    except RepoConfigNotFoundError:
        return None

    return repo_root / ".mcodex" / "templates"


def _package_templates_root(exit_stack: ExitStack) -> Path:
    traversable = importlib.resources.files("mcodex.package_templates").joinpath(
        "templates"
    )
    src = exit_stack.enter_context(importlib.resources.as_file(traversable))
    return Path(src)


def _templates_root(source_dir: Path, exit_stack: ExitStack) -> Path:
    repo_root = _repo_templates_root(source_dir)
    if repo_root is not None:
        return repo_root
    return _package_templates_root(exit_stack)


def _pandoc_template_args(*, templates_root: Path, to: str) -> list[str]:
    pandoc_dir = templates_root / "pandoc"
    if not pandoc_dir.exists():
        return []

    args: list[str] = []

    if to == "docx":
        ref = pandoc_dir / "reference.docx"
        if ref.exists() and ref.is_file():
            args.append(f"--reference-doc={ref}")

    if to == "pdf":
        tex_tmpl = pandoc_dir / "template.tex"
        if tex_tmpl.exists() and tex_tmpl.is_file():
            args.append(f"--template={tex_tmpl}")

    return args


def _latex_templates_dir(templates_root: Path) -> Path:
    return templates_root / "latex"


def run_pipeline(
    *,
    pipeline_name: str,
    source_dir: Path,
    output_path: Path,
    dry_run: bool = False,
    run: RunFn | None = None,
    version_label: str = "worktree",
) -> PipelineResult:
    """Execute a configured pipeline.

    The pipeline is taken from `.mcodex/config.yaml` if `source_dir` is in a
    mcodex repo; otherwise `DEFAULT_PIPELINES` are used.

    Templates are resolved from `.mcodex/templates/...` when running inside a
    repo and from packaged defaults otherwise.
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

    with ExitStack() as stack:
        templates_root = _templates_root(source_dir, stack)

        with tempfile.TemporaryDirectory(prefix="mcodex-build-") as td:
            tmp = Path(td)

            write_build_context(
                tmp_dir=tmp,
                source_dir=source_dir,
                pipeline_name=pipeline_name,
                version_label=version_label,
            )

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
                        f"--metadata-file={tmp / 'build_context.yaml'}",
                        *_pandoc_template_args(templates_root=templates_root, to=to),
                        *(
                            [f"--include-before-body={tmp / 'build_header.md'}"]
                            if to in {"pdf", "docx"}
                            else []
                        ),
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

                        latex_dir = _latex_templates_dir(templates_root)
                        _copy_dir_contents(latex_dir, tmp)

                        main = tmp / main_name
                        if not main.exists():
                            raise FileNotFoundError(
                                f"LaTeX main template not found after copying: {main}"
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
                        str(main_name),
                    ]
                    commands.append(cmd)
                    if not dry_run:
                        runner(cmd, tmp)

                    built_pdf = tmp / "main.pdf"
                    if not dry_run and not built_pdf.exists():
                        raise RuntimeError(
                            "latexmk finished without producing main.pdf"
                        )

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
