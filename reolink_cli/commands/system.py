"""System administration commands — reboot, firmware, time, users."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from typing import TYPE_CHECKING

from reolink_cli.client import EXIT_USAGE
from reolink_cli.output import output, print_error

if TYPE_CHECKING:
    from reolink_cli.client import ReolinkClient


# ---------------------------------------------------------------------------
# Reboot
# ---------------------------------------------------------------------------

def _cmd_reboot(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Reboot the camera."""
    if not args.force:
        print_error("Reboot requires --force flag. This will restart the camera.")
        sys.exit(EXIT_USAGE)

    client.reboot()
    if args.json:
        output({"reboot": "initiated"}, json_mode=True)
    else:
        print("Camera reboot initiated.")


# ---------------------------------------------------------------------------
# Firmware
# ---------------------------------------------------------------------------

def _cmd_firmware_info(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Show current firmware information."""
    raw = client.get_firmware_info()

    if args.json:
        output(raw, json_mode=True)
        return

    display: dict[str, str] = {}
    if "firmVer" in raw:
        display["Firmware"] = raw["firmVer"]
    if "model" in raw:
        display["Model"] = raw["model"]
    if "hardVer" in raw:
        display["Hardware"] = raw["hardVer"]
    if "buildDay" in raw:
        display["Build Date"] = raw["buildDay"]
    output(display, title="Firmware Info")


def _cmd_firmware_check(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Check for firmware updates."""
    raw = client.check_firmware()

    if args.json:
        output(raw, json_mode=True)
        return

    display: dict[str, str] = {}
    if "firmVer" in raw:
        display["Current"] = raw["firmVer"]
    if "newFirmVer" in raw:
        display["Available"] = raw["newFirmVer"]
    need = raw.get("needUpgrade", 0)
    display["Update Available"] = "Yes" if need else "No"
    output(display, title="Firmware Update")


def _cmd_firmware_update(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Start online firmware upgrade."""
    if not args.force:
        print_error("Firmware update requires --force flag. This will update camera firmware.")
        sys.exit(EXIT_USAGE)

    client.upgrade_online()
    if args.json:
        output({"firmware_update": "initiated"}, json_mode=True)
    else:
        print("Firmware update initiated. Camera will reboot when complete.")


# ---------------------------------------------------------------------------
# Time
# ---------------------------------------------------------------------------

def _cmd_time_set(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Set system time."""
    try:
        dt = datetime.fromisoformat(args.datetime)
    except ValueError:
        print_error(f"Invalid datetime format: {args.datetime} (use ISO format, e.g. 2026-02-10T14:30:00)")
        sys.exit(EXIT_USAGE)

    time_dict = {
        "Time": {
            "year": dt.year,
            "mon": dt.month,
            "day": dt.day,
            "hour": dt.hour,
            "min": dt.minute,
            "sec": dt.second,
        }
    }

    tz = getattr(args, "timezone", None)
    if tz is not None:
        time_dict["Time"]["timeZone"] = tz * 3600

    client.set_time(time_dict)
    if args.json:
        output(time_dict, json_mode=True)
    else:
        print(f"System time set to {dt.isoformat()}.")


# ---------------------------------------------------------------------------
# NTP
# ---------------------------------------------------------------------------

def _cmd_ntp_status(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Show NTP configuration."""
    raw = client.get_ntp()

    if args.json:
        output(raw, json_mode=True)
        return

    display: dict[str, str] = {}
    if "enable" in raw:
        display["NTP"] = "Enabled" if raw["enable"] == 1 else "Disabled"
    if "server" in raw:
        display["Server"] = raw["server"]
    if "port" in raw:
        display["Port"] = str(raw["port"])
    if "interval" in raw:
        display["Interval"] = f"{raw['interval']} min"
    output(display, title="NTP")


def _cmd_ntp_set(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Set NTP configuration."""
    kwargs: dict = {}
    if getattr(args, "server", None) is not None:
        kwargs["server"] = args.server
    if getattr(args, "port", None) is not None:
        kwargs["port"] = args.port
    if getattr(args, "ntp_enable", None) is not None:
        kwargs["enable"] = 1 if args.ntp_enable else 0
    client.set_ntp(**kwargs)
    if args.json:
        output(kwargs, json_mode=True)
    else:
        print("NTP configuration updated.")


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def _cmd_users_list(args: argparse.Namespace, client: ReolinkClient) -> None:
    """List users and online sessions."""
    users = client.get_user()
    online = client.get_online()

    if args.json:
        output({"users": users, "online": online}, json_mode=True)
        return

    online_names = {s.get("userName") for s in online}
    print("Users:")
    for u in users:
        name = u.get("userName", "?")
        level = u.get("level", "?")
        status = " (online)" if name in online_names else ""
        print(f"  {name:20s}  {level:10s}{status}")


def _cmd_users_add(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Add a new user."""
    client.add_user(args.username, args.userpass, level=args.level)
    if args.json:
        output({"user_added": args.username, "level": args.level}, json_mode=True)
    else:
        print(f"User '{args.username}' added with level '{args.level}'.")


def _cmd_users_delete(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Delete a user."""
    if not args.force:
        print_error(f"Deleting user '{args.username}' requires --force flag.")
        sys.exit(EXIT_USAGE)

    client.delete_user(args.username)
    if args.json:
        output({"user_deleted": args.username}, json_mode=True)
    else:
        print(f"User '{args.username}' deleted.")


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register system administration commands with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    # reboot
    reboot_parser = subparsers.add_parser("reboot", help="Reboot the camera")
    reboot_parser.add_argument("--force", action="store_true", help="Confirm reboot")
    reboot_parser.set_defaults(func=_cmd_reboot)

    # firmware
    fw_parser = subparsers.add_parser("firmware", help="Firmware management")
    fw_parser.set_defaults(func=_cmd_firmware_info)
    fw_sub = fw_parser.add_subparsers(dest="firmware_command")
    fw_info = fw_sub.add_parser("info", help="Show firmware information")
    fw_info.set_defaults(func=_cmd_firmware_info)
    fw_check = fw_sub.add_parser("check", help="Check for firmware updates")
    fw_check.set_defaults(func=_cmd_firmware_check)
    fw_update = fw_sub.add_parser("update", help="Start firmware update")
    fw_update.add_argument("--force", action="store_true", help="Confirm firmware update")
    fw_update.set_defaults(func=_cmd_firmware_update)

    # time set (extends existing time command — register under 'time' subparsers)
    # Note: 'time' is already registered by device.py. We add 'time set' here.
    # This is handled via the time_sub subparser added in device.py register.

    # ntp
    ntp_parser = subparsers.add_parser("ntp", help="NTP time sync")
    ntp_parser.set_defaults(func=_cmd_ntp_status)
    ntp_sub = ntp_parser.add_subparsers(dest="ntp_command")
    ntp_status = ntp_sub.add_parser("status", help="Show NTP configuration")
    ntp_status.set_defaults(func=_cmd_ntp_status)
    ntp_set = ntp_sub.add_parser("set", help="Set NTP configuration")
    ntp_set.add_argument("--server", metavar="HOST", help="NTP server hostname")
    ntp_set.add_argument("--port", type=int, metavar="N", help="NTP server port")
    ntp_set.add_argument("--enable", dest="ntp_enable", action="store_true", default=None,
                         help="Enable NTP")
    ntp_set.add_argument("--disable", dest="ntp_enable", action="store_false",
                         help="Disable NTP")
    ntp_set.set_defaults(func=_cmd_ntp_set)

    # users
    users_parser = subparsers.add_parser("users", help="User management")
    users_parser.set_defaults(func=_cmd_users_list)
    users_sub = users_parser.add_subparsers(dest="users_command")
    users_list = users_sub.add_parser("list", help="List users")
    users_list.set_defaults(func=_cmd_users_list)
    users_add = users_sub.add_parser("add", help="Add a user")
    users_add.add_argument("username", help="New username")
    users_add.add_argument("userpass", help="New password")
    users_add.add_argument(
        "--level", choices=["admin", "guest"], default="guest",
        help="Permission level (default: guest)",
    )
    users_add.set_defaults(func=_cmd_users_add)
    users_del = users_sub.add_parser("delete", help="Delete a user")
    users_del.add_argument("username", help="Username to delete")
    users_del.add_argument("--force", action="store_true", help="Confirm deletion")
    users_del.set_defaults(func=_cmd_users_delete)
