from __future__ import annotations

import os
from pathlib import Path


def before_scenario(context, scenario) -> None:
    context.workdir = Path(context.base_dir) / ".behave-work"
    context.workdir.mkdir(parents=True, exist_ok=True)

    context.cfg_path = context.workdir / "config.yaml"
    os.environ["MCODEX_CONFIG_PATH"] = str(context.cfg_path)


def after_scenario(context, scenario) -> None:
    os.environ.pop("MCODEX_CONFIG_PATH", None)
