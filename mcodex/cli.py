from __future__ import annotations

from pathlib import Path

from docopt import docopt

from mcodex.services.author import author_add, author_list, author_remove
from mcodex.services.create_text import create_text
from mcodex.services.snapshot import snapshot_create, snapshot_list
from mcodex.services.status import show_status
from mcodex.services.text_authors import text_author_add, text_author_remove

__version__ = "0.1.0"

_DOC = """
mcodex

Usage:
  mcodex create <title> [--root=<dir>] --author=<nickname>...
  mcodex author add <nickname> <first_name> <last_name> <email>
  mcodex author remove <nickname>
  mcodex author list
  mcodex text author add <text_dir> <nickname>
  mcodex text author remove <text_dir> <nickname>
  mcodex snapshot create <text_dir> <stage> [--note=<text>]
  mcodex snapshot list <text_dir>
  mcodex status <text_dir>
  mcodex (-h | --help)
  mcodex --version

Options:
  --root=<dir>   Target directory where the new text folder will be created
                 [default: .]
  --author=<nickname>  Author nickname (repeatable).
  --note=<text>  Optional note stored with the snapshot.
  -h --help      Show this screen.
  --version      Show version.

Notes:
  Values with spaces must be quoted, e.g.:
    mcodex author add jan "Jan" "Novák" jan@example.com

Stages:
  draft | preview | rc | final | published
"""


def main(argv: list[str] | None = None) -> int:
    args = docopt(_DOC, argv=argv, version=f"mcodex {__version__}")

    if args["author"] and args["add"]:
        author_add(
            nickname=args["<nickname>"],
            first_name=args["<first_name>"],
            last_name=args["<last_name>"],
            email=args["<email>"],
        )
        return 0

    if args["author"] and args["remove"]:
        author_remove(nickname=args["<nickname>"])
        return 0

    if args["author"] and args["list"]:
        author_list()
        return 0

    if args["text"] and args["author"] and args["add"]:
        text_author_add(text_dir=Path(args["<text_dir>"]), nickname=args["<nickname>"])
        return 0

    if args["text"] and args["author"] and args["remove"]:
        text_author_remove(
            text_dir=Path(args["<text_dir>"]),
            nickname=args["<nickname>"],
        )
        return 0

    if args["snapshot"] and args["create"]:
        snap_dir = snapshot_create(
            text_dir=Path(args["<text_dir>"]),
            stage=args["<stage>"],
            note=args["--note"],
        )
        print(f"Snapshot created: {snap_dir.name}")
        return 0

    if args["snapshot"] and args["list"]:
        snapshot_list(text_dir=Path(args["<text_dir>"]))
        return 0

    if args["status"]:
        show_status(text_dir=Path(args["<text_dir>"]))
        return 0

    if args["create"] and not args["snapshot"]:
        title: str = args["<title>"]
        root_dir: str = args["--root"]
        nicknames: list[str] = args["--author"]
        create_text(title=title, root=Path(root_dir), author_nicknames=nicknames)
        return 0

    raise AssertionError("Unhandled command arguments.")
