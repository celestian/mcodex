from __future__ import annotations

import sys

from mcodex.cli import main as cli_main
from mcodex.errors import McodexError


def main(argv: list[str] | None = None) -> int:
    try:
        return cli_main(argv)
    except McodexError as exc:
        print(f"mcodex: error: {exc}", file=sys.stderr)
        raise SystemExit(2) from None
    except KeyboardInterrupt:
        raise SystemExit(130) from None
