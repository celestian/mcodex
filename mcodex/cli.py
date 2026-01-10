from __future__ import annotations

from pathlib import Path

from docopt import docopt

from mcodex.cli_utils import locate_text_dir_for_build, locate_text_dir_for_snapshot
from mcodex.path_utils import normalize_path
from mcodex.services.author import author_add, author_list, author_remove
from mcodex.services.build import build
from mcodex.services.create_text import create_text
from mcodex.services.init_repo import init_repo
from mcodex.services.pipeline_list import pipeline_list
from mcodex.services.snapshot import snapshot_create, snapshot_list
from mcodex.services.status import show_status
from mcodex.services.text_authors import text_author_add, text_author_remove
from mcodex.version import get_version

_DOC = """
mcodex

Usage:
  mcodex init [--root=<dir>] [--force]
  mcodex create <title> [--root=<dir>] --author=<nickname>...
  mcodex author add <nickname> <first_name> <last_name> <email>
  mcodex author remove <nickname>
  mcodex author list
  mcodex text author add <text_dir> <nickname>
  mcodex text author remove <text_dir> <nickname>
  mcodex pipeline list
  mcodex build [<text>] [<ref>] [--pipeline=<name>]
  mcodex snapshot <label> [--note=<note>]
  mcodex snapshot <text> <label> [--note=<note>]
  mcodex snapshot list
  mcodex snapshot list <text>
  mcodex status [<text_dir>]
  mcodex (-h | --help)
  mcodex --version

Options:
  --root=<dir>   Target directory used by `init` and `create`, and as a lookup
                 root for `create`.
                 [default: .]
  --force        Overwrite existing template files when running `init`.
  --author=<nickname>  Author nickname (repeatable).
  --note=<note>  Optional note stored with the snapshot.
  --pipeline=<name>  Build pipeline to use. [default: pdf]
  -h --help      Show this screen.
  --version      Show version.

Build:
  <ref> is '.' for worktree, or a snapshot label.

  Context-aware argument resolution:
    - Inside a text directory:
        mcodex build            -> uses <ref>='.'
        mcodex build <ref>      -> builds that ref for current text
    - Inside a repo (outside a text directory):
        mcodex build <text>     -> builds worktree for that text
        mcodex build <text> <ref>
    - Outside a repo:
        mcodex build <path> [<ref>]

Snapshot:
  <text> is optional when run inside a text directory.
  In a mcodex repo, <text> is the logical slug (without the text_ prefix).
  Outside a repo, <text> must be a path.
"""


def main(argv: list[str] | None = None) -> int:
    args = docopt(_DOC, argv=argv, version=f"mcodex {get_version()}")

    if args.get("init"):
        root = normalize_path(Path(args["--root"]))
        init_repo(root, force=bool(args["--force"]))
        print(f"Initialized mcodex in: {root}")
        return 0

    if args.get("pipeline") and args.get("list"):
        pipeline_list()
        return 0

    # IMPORTANT: "text author ..." also sets args["author"] to True.
    # Handle the more specific "text author" commands first.
    if args["text"] and args["author"] and args["add"]:
        text_author_add(
            text_dir=Path(args["<text_dir>"]),
            nickname=args["<nickname>"],
        )
        return 0

    if args["text"] and args["author"] and args["remove"]:
        text_author_remove(
            text_dir=Path(args["<text_dir>"]),
            nickname=args["<nickname>"],
        )
        return 0

    if args["author"] and args["add"] and not args["text"]:
        author_add(
            nickname=args["<nickname>"],
            first_name=args["<first_name>"],
            last_name=args["<last_name>"],
            email=args["<email>"],
        )
        return 0

    if args["author"] and args["remove"] and not args["text"]:
        author_remove(nickname=args["<nickname>"])
        return 0

    if args["author"] and args["list"] and not args["text"]:
        author_list()
        return 0

    if args["build"]:
        text = args["<text>"]
        ref = args["<ref>"]
        pipeline = args["--pipeline"]

        text_dir, resolved_ref = locate_text_dir_for_build(text=text, ref=ref)
        out = build(text_dir=text_dir, ref=resolved_ref, pipeline=pipeline)
        print(out)
        return 0

    if args["snapshot"] and not args["list"]:
        text_dir = locate_text_dir_for_snapshot(text=args["<text>"])
        snap_dir = snapshot_create(
            text_dir=text_dir,
            label=args["<label>"],
            note=args["--note"],
        )
        print(f"Snapshot created: {snap_dir.name}")
        return 0

    if args["snapshot"] and args["list"]:
        text_dir = locate_text_dir_for_snapshot(text=args["<text>"])
        snapshot_list(text_dir=text_dir)
        return 0

    if args["status"]:
        from mcodex.cli_utils import resolve_text_dir

        text_dir = resolve_text_dir(args["<text_dir>"])
        show_status(text_dir=text_dir)
        return 0

    if args["create"] and not args["snapshot"]:
        create_text(
            title=args["<title>"],
            root=Path(args["--root"]),
            author_nicknames=args["--author"],
        )
        return 0

    raise AssertionError("Unhandled command arguments.")
