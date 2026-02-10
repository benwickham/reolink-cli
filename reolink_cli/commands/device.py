"""Device information commands."""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

from reolink_cli.output import output

if TYPE_CHECKING:
    from reolink_cli.client import ReolinkClient


# Fields to display and their human-readable labels
_INFO_FIELDS = {
    "name": "Name",
    "model": "Model",
    "firmVer": "Firmware",
    "hardVer": "Hardware",
    "serial": "Serial",
    "uid": "UID",
    "channelNum": "Channels",
    "buildDay": "Build Date",
    "cfgVer": "Config Version",
    "detail": "Detail",
    "pakSuffix": "Package Suffix",
    "exactType": "Type",
    "B485": "RS485",
    "wifi": "WiFi",
    "IOInputNum": "IO Inputs",
    "IOOutputNum": "IO Outputs",
    "diskNum": "Disk Count",
}


def _cmd_info(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Show device information."""
    raw = client.get_device_info()

    if args.json:
        output(raw, json_mode=True)
        return

    # Build display dict with human labels, skipping missing fields
    display: dict[str, str] = {}
    for key, label in _INFO_FIELDS.items():
        if key in raw:
            display[label] = raw[key]
    output(display, title="Device Info")


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register device commands with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    info_parser = subparsers.add_parser("info", help="Show device information")
    info_parser.set_defaults(func=_cmd_info)
