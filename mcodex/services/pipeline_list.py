from __future__ import annotations

from pathlib import Path
from typing import Any

from mcodex.config import get_pipelines, validate_pipelines
from mcodex.errors import PipelineConfigError


def pipeline_list(*, start: Path | None = None) -> None:
    pipelines = get_pipelines(start=start)
    if not pipelines:
        print("No pipelines configured in .mcodex/config.yaml.")
        return

    validate_pipelines(pipelines)

    names = sorted(str(k) for k in pipelines.keys())
    for name in names:
        suffix = " (default)" if name == "pdf" else ""
        print(f"{name}{suffix}")

        pipe = pipelines[name]
        steps = pipe.get("steps", [])
        for step in steps:
            print(f"  - {_format_step(step)}")


def _format_step(step: dict[str, Any]) -> str:
    kind = str(step.get("kind") or "").strip()

    if kind == "pandoc":
        from_ = str(step.get("from") or "").strip()
        to = str(step.get("to") or "").strip()
        out = step.get("output")
        out_s = f" output={out}" if isinstance(out, str) and out.strip() else ""
        return f"pandoc {from_} -> {to}{out_s}"

    if kind == "vlna":
        inp = str(step.get("input") or "").strip()
        out = str(step.get("output") or "").strip()
        return f"vlna {inp} -> {out}"

    if kind == "latexmk":
        engine = step.get("engine")
        condition = isinstance(engine, str) and engine.strip()
        eng_s = f" engine={engine}" if condition else ""
        main = str(step.get("main") or "").strip()
        return f"latexmk{eng_s} main={main}"

    raise PipelineConfigError(f"Unknown pipeline step kind: {kind}")
