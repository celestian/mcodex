from __future__ import annotations

from pathlib import Path

from mcodex.services.snapshot import available_stages, current_stage


def show_status(*, text_dir: Path) -> None:
    tdir = text_dir.expanduser().resolve()
    if not tdir.exists():
        raise FileNotFoundError(f"Text directory does not exist: {tdir}")
    if not tdir.is_dir():
        raise NotADirectoryError(f"Text path is not a directory: {tdir}")

    cur = current_stage(text_dir=tdir)
    if cur is None:
        print("Current stage: none")
    else:
        print(f"Current stage: {cur}")

    stages = available_stages(text_dir=tdir)
    print("Available stages:")
    for s in stages:
        print(f"  - {s}")
