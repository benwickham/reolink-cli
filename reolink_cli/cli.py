"""CLI entry point — placeholder for Phase 1."""

import argparse
import sys

from reolink_cli import __version__


def main():
    parser = argparse.ArgumentParser(
        prog="reolink",
        description="Command-line interface for controlling Reolink cameras.",
    )
    parser.add_argument("--version", action="version", version=f"reolink-cli {__version__}")
    parser.parse_args()
    parser.print_help()
    sys.exit(0)


if __name__ == "__main__":
    main()
