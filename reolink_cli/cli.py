"""CLI entry point — argparse setup, subcommand routing, main()."""

from __future__ import annotations

import argparse
import os
import sys

from reolink_cli import __version__
from reolink_cli.client import (
    EXIT_AUTH,
    EXIT_ERROR,
    EXIT_UNREACHABLE,
    EXIT_USAGE,
    AuthError,
    NetworkError,
    ReolinkClient,
    ReolinkError,
)
from reolink_cli.commands import alerts, controls, detection, device, media, system
from reolink_cli.output import print_error


def _build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser with global flags and subcommands."""
    parser = argparse.ArgumentParser(
        prog="reolink",
        description="Command-line interface for controlling Reolink cameras.",
    )
    parser.add_argument(
        "--version", action="version", version=f"reolink-cli {__version__}",
    )
    parser.add_argument(
        "--host", metavar="HOST",
        default=os.environ.get("REOLINK_HOST"),
        help="Camera IP or hostname (env: REOLINK_HOST)",
    )
    parser.add_argument(
        "--user", metavar="USER",
        default=os.environ.get("REOLINK_USER", "admin"),
        help="Username (default: admin, env: REOLINK_USER)",
    )
    parser.add_argument(
        "--password", metavar="PASS", dest="password",
        default=os.environ.get("REOLINK_PASS"),
        help="Password (env: REOLINK_PASS)",
    )
    parser.add_argument(
        "--channel", metavar="CH", type=int,
        default=int(os.environ.get("REOLINK_CHANNEL", "0")),
        help="Channel index (default: 0, env: REOLINK_CHANNEL)",
    )
    parser.add_argument(
        "--timeout", metavar="SEC", type=int, default=10,
        help="Request timeout in seconds (default: 10)",
    )
    parser.add_argument(
        "--json", action="store_true", default=False,
        help="Output as JSON",
    )
    parser.add_argument(
        "--quiet", action="store_true", default=False,
        help="Suppress informational output",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND",
                                       title="commands")
    device.register(subparsers)
    media.register(subparsers)
    detection.register(subparsers)
    controls.register(subparsers)
    alerts.register(subparsers)
    system.register(subparsers)

    return parser


def _make_client(args: argparse.Namespace) -> ReolinkClient:
    """Create a ReolinkClient from parsed CLI args.

    Args:
        args: Parsed argument namespace with host, user, password, channel, timeout.

    Returns:
        Configured ReolinkClient instance.
    """
    if not args.host:
        print_error("--host is required (or set REOLINK_HOST)")
        sys.exit(EXIT_USAGE)
    if not args.password:
        print_error("--password is required (or set REOLINK_PASS)")
        sys.exit(EXIT_USAGE)
    return ReolinkClient(
        host=args.host,
        password=args.password,
        username=args.user,
        channel=args.channel,
        timeout=args.timeout,
    )


def main(argv: list[str] | None = None) -> None:
    """CLI entry point.

    Args:
        argv: Command-line arguments (default: sys.argv[1:]).
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        sys.exit(EXIT_USAGE)

    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        sys.exit(EXIT_USAGE)

    client = _make_client(args)
    try:
        with client:
            func(args, client)
    except AuthError as exc:
        print_error(str(exc))
        sys.exit(EXIT_AUTH)
    except NetworkError as exc:
        print_error(str(exc))
        sys.exit(EXIT_UNREACHABLE)
    except ReolinkError as exc:
        print_error(str(exc))
        sys.exit(exc.exit_code)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
