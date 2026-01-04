from __future__ import annotations

from pathlib import Path

from docopt import docopt

from mcodex.cli_utils import locate_text_dir
from mcodex.services.author import author_add, author_list, author_remove
from mcodex.services.build import build_pdf
from mcodex.services.create_text import create_text
from mcodex.services.init_repo import init_repo
from mcodex.services.snapshot import snapshot_create, snapshot_list
from mcodex.services.status import show_status
from mcodex.services.text_authors import text_author_add, text_author_remove

__version__ = "0.1.0"

_DOC = """
mcodex

Usage:
  mcodex init [--root=<dir>]
  mcodex create <title> [--root=<dir>] --author=<nickname>...
  mcodex author add <nickname> <first_name> <last_name> <email>
  mcodex author remove <nickname>
  mcodex author list
  mcodex text author add <text_dir> <nickname>
  mcodex text author remove <text_dir> <nickname>
  mcodex build [<slug>] [<version>] [--root=<dir>]
  mcodex snapshot create <stage> [<text_dir>] [--note=<text>]
  mcodex snapshot list [<text_dir>]
  mcodex status [<text_dir>]
  mcodex (-h | --help)
  mcodex --version

Options:
  --root=<dir>   Target directory used by `init` and `create`, and as a lookup
                 root for `build`.
                 [default: .]
  --author=<nickname>  Author nickname (repeatable).
  --note=<text>  Optional note stored with the snapshot.
  -h --help      Show this screen.
  --version      Show version.

Build:
  <slug> is the text folder name under --root (default: .).
  <version> is '.' for worktree, or a snapshot label.
  When run inside a text directory, a single positional arg is treated
  as <version>.

Snapshot stages:
  draft | preview | rc | final | published
"""


def main(argv: list[str] | None = None) -> int:
    args = docopt(_DOC, argv=argv, version=f"mcodex {__version__}")

    if args.get("init"):
        root = Path(args["--root"]).expanduser().resolve()
        init_repo(root)
        print(f"Initialized mcodex in: {root}")
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
        root = Path(args["--root"]).expanduser().resolve()
        slug = args["<slug>"]
        version = args["<version>"]

        text_dir, resolved_version = locate_text_dir(
            root=root,
            slug=slug,
            version=version,
        )
        out = build_pdf(text_dir=text_dir, version=resolved_version)
        print(out)
        return 0

    if args["snapshot"] and args["create"]:
        from mcodex.cli_utils import resolve_text_dir

        text_dir = resolve_text_dir(args["<text_dir>"])
        snap_dir = snapshot_create(
            text_dir=text_dir,
            stage=args["<stage>"],
            note=args["--note"],
        )
        print(f"Snapshot created: {snap_dir.name}")
        return 0

    if args["snapshot"] and args["list"]:
        from mcodex.cli_utils import resolve_text_dir

        text_dir = resolve_text_dir(args["<text_dir>"])
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
