from __future__ import annotations

import sys

from mcodex.cli import main as cli_main


def main(argv: list[str] | None = None) -> int:
    return cli_main(argv)


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (ValueError, FileNotFoundError, NotADirectoryError, FileExistsError) as exc:
        print(f"mcodex: error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    except KeyboardInterrupt:
        raise SystemExit(130) from None
