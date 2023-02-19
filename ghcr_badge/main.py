"""Main script."""

from __future__ import annotations

from argparse import (
    ArgumentDefaultsHelpFormatter,
    ArgumentParser,
    ArgumentTypeError,
    Namespace,
    RawDescriptionHelpFormatter,
)
from http.client import CannotSendRequest, HTTPConnection
from pathlib import Path
from shutil import get_terminal_size

from . import GHCRBadgeGenerator, __version__


class HttpConnectionNotFountError(Exception):
    """Raise if offline."""


class HelpFormatter(ArgumentDefaultsHelpFormatter, RawDescriptionHelpFormatter):
    """Help formatter for argparse."""


def check_connectivity(url: str = "www.google.com", timeout: int = 3) -> bool:
    """Check connectivity.

    Parameters
    ----------
    url : str, optional
        site URL, by default "www.google.com"
    timeout : int, optional
        second to wait, by default 3

    Returns
    -------
    bool
        True if online.
    """
    conn = HTTPConnection(url, timeout=timeout)
    try:
        conn.request("HEAD", "/")
        conn.close()
    except CannotSendRequest as e:
        msg = "No connection."
        raise ArgumentTypeError(msg) from e

    return True


def parse_args(test: list[str] | None = None) -> Namespace:
    """Parse arguments."""
    parser = ArgumentParser(
        prog="ghcr-badge",
        formatter_class=(
            lambda prog: HelpFormatter(
                prog,
                width=get_terminal_size(fallback=(120, 50)).columns,
                max_help_position=25,
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
    return parser.parse_args(args=test)


def main() -> None:
    """Execute main script.

    Raises
    ------
    HttpConnectionNotFountError
        raise if offline
    """
    args = parse_args()
    color = str(args.color)
    user = str(args.user)
    name = str(args.name)
    out = Path(args.out)
    if not check_connectivity():
        raise HttpConnectionNotFountError
    g = GHCRBadgeGenerator(color=color)
    data = g.generate_tags(user, name)
    if args.out:
        print(data, file=out.open("w"))
    else:
        print(data)  # noqa: T201


if __name__ == "__main__":
    main()
