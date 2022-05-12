from __future__ import annotations

import argparse
import http.client as httplib
import sys
from shutil import get_terminal_size

from . import GHCRBadgeGenerator, __version__


class HttpConnectionNotFountError(Exception):
    pass


class HelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter
):
    pass


def check_connectivity(url: str = "www.google.com", timeout: int = 3) -> bool:
    conn = httplib.HTTPConnection(url, timeout=timeout)
    try:
        conn.request("HEAD", "/")
        conn.close()
        return True
    except Exception as e:
        print(e, file=sys.stderr)
        return False


def parse_args(test: list[str] | None = None) -> argparse.Namespace:
    """Parse arguments."""
    parser = argparse.ArgumentParser(
        prog="ghcr-badge",
        formatter_class=(
            lambda prog: HelpFormatter(
                prog,
                **{
                    "width": get_terminal_size(fallback=(120, 50)).columns,
                    "max_help_position": 25,
                },
            )
        ),
        description="Generate ghcr.io container's status badge",
    )
    parser.add_argument(
        "-u",
        "--user",
        required=True,
        metavar="ID",
        help="container owner",
    )
    parser.add_argument(
        "-n",
        "--name",
        type=str,
        metavar="NAME",
        required=True,
        help="container name",
    )
    parser.add_argument(
        "-c",
        "--color",
        type=str,
        metavar="COLOR",
        default="lime",
        help="badge color",
    )
    parser.add_argument(
        "-o",
        "--out",
        type=str,
        metavar="PATH",
        help="save path",
    )
    parser.add_argument("-V", "--version", action="version", version=__version__)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not check_connectivity():
        raise HttpConnectionNotFountError
    g = GHCRBadgeGenerator(args.color)
    data = g.generate_tags(args.user, args.name)
    if args.out:
        print(data, file=open(args.out, "w"))
    else:
        print(data)


if __name__ == "__main__":
    main()
