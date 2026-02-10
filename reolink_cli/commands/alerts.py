"""Siren, push, FTP, email, and recording toggle commands."""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

from reolink_cli.output import output

if TYPE_CHECKING:
    from reolink_cli.client import ReolinkClient


# ---------------------------------------------------------------------------
# Siren
# ---------------------------------------------------------------------------

def _cmd_siren_trigger(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Trigger the siren / audio alarm."""
    duration = getattr(args, "duration", 0) or 0
    if duration:
        client.audio_alarm_play(alarm_mode="times", manual_switch=1, duration=duration)
    else:
        client.audio_alarm_play(manual_switch=1)
    if args.json:
        output({"siren": "triggered", "duration": duration}, json_mode=True)
    else:
        msg = f"Siren triggered for {duration}s." if duration else "Siren triggered."
        print(msg)


def _cmd_siren_stop(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Stop the siren / audio alarm."""
    client.audio_alarm_play(manual_switch=0)
    if args.json:
        output({"siren": "stopped"}, json_mode=True)
    else:
        print("Siren stopped.")


# ---------------------------------------------------------------------------
# Push notifications
# ---------------------------------------------------------------------------

def _cmd_push_status(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Show push notification configuration."""
    raw = client.get_push()

    if args.json:
        output(raw, json_mode=True)
        return

    display: dict[str, str] = {}
    if "enable" in raw:
        display["Push Notifications"] = "Enabled" if raw["enable"] == 1 else "Disabled"
    output(display, title="Push Notifications")


def _cmd_push_set(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Enable or disable push notifications."""
    enable = args.action == "enable"
    client.set_push(enable=enable)
    state = "enabled" if enable else "disabled"
    if args.json:
        output({"push": state}, json_mode=True)
    else:
        print(f"Push notifications {state}.")


# ---------------------------------------------------------------------------
# FTP
# ---------------------------------------------------------------------------

def _cmd_ftp_status(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Show FTP upload configuration."""
    raw = client.get_ftp()

    if args.json:
        output(raw, json_mode=True)
        return

    display: dict[str, str] = {}
    if "enable" in raw:
        display["FTP Upload"] = "Enabled" if raw["enable"] == 1 else "Disabled"
    if "server" in raw:
        display["Server"] = raw["server"]
    if "port" in raw:
        display["Port"] = str(raw["port"])
    output(display, title="FTP Upload")


def _cmd_ftp_set(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Enable or disable FTP upload."""
    enable = args.action == "enable"
    client.set_ftp(enable=enable)
    state = "enabled" if enable else "disabled"
    if args.json:
        output({"ftp": state}, json_mode=True)
    else:
        print(f"FTP upload {state}.")


def _cmd_ftp_test(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Test FTP connection."""
    client.test_ftp()
    if args.json:
        output({"ftp_test": "ok"}, json_mode=True)
    else:
        print("FTP test successful.")


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

def _cmd_email_status(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Show email alert configuration."""
    raw = client.get_email()

    if args.json:
        output(raw, json_mode=True)
        return

    display: dict[str, str] = {}
    if "enable" in raw:
        display["Email Alerts"] = "Enabled" if raw["enable"] == 1 else "Disabled"
    if "addr1" in raw:
        display["Recipient"] = raw["addr1"]
    if "smtpServer" in raw:
        display["SMTP Server"] = raw["smtpServer"]
    output(display, title="Email Alerts")


def _cmd_email_set(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Enable or disable email alerts."""
    enable = args.action == "enable"
    client.set_email(enable=enable)
    state = "enabled" if enable else "disabled"
    if args.json:
        output({"email": state}, json_mode=True)
    else:
        print(f"Email alerts {state}.")


def _cmd_email_test(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Test email delivery."""
    client.test_email()
    if args.json:
        output({"email_test": "ok"}, json_mode=True)
    else:
        print("Email test successful.")


# ---------------------------------------------------------------------------
# Recording toggle
# ---------------------------------------------------------------------------

def _cmd_recording_set(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Enable or disable recording."""
    enable = args.action == "enable"
    client.set_rec(enable=enable)
    state = "enabled" if enable else "disabled"
    if args.json:
        output({"recording": state}, json_mode=True)
    else:
        print(f"Recording {state}.")


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register alert and notification commands with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    # siren
    siren_parser = subparsers.add_parser("siren", help="Siren / audio alarm")
    siren_sub = siren_parser.add_subparsers(dest="siren_command")
    siren_trigger = siren_sub.add_parser("trigger", help="Trigger the siren")
    siren_trigger.add_argument(
        "--duration", type=int, default=0, metavar="SEC",
        help="Duration in seconds (0 = until stopped)",
    )
    siren_trigger.set_defaults(func=_cmd_siren_trigger)
    siren_stop = siren_sub.add_parser("stop", help="Stop the siren")
    siren_stop.set_defaults(func=_cmd_siren_stop)

    # push
    push_parser = subparsers.add_parser("push", help="Push notifications")
    push_parser.set_defaults(func=_cmd_push_status)
    push_sub = push_parser.add_subparsers(dest="push_command")
    push_status = push_sub.add_parser("status", help="Show push notification status")
    push_status.set_defaults(func=_cmd_push_status)
    push_enable = push_sub.add_parser("enable", help="Enable push notifications")
    push_enable.set_defaults(func=_cmd_push_set, action="enable")
    push_disable = push_sub.add_parser("disable", help="Disable push notifications")
    push_disable.set_defaults(func=_cmd_push_set, action="disable")

    # ftp
    ftp_parser = subparsers.add_parser("ftp", help="FTP upload")
    ftp_parser.set_defaults(func=_cmd_ftp_status)
    ftp_sub = ftp_parser.add_subparsers(dest="ftp_command")
    ftp_status = ftp_sub.add_parser("status", help="Show FTP status")
    ftp_status.set_defaults(func=_cmd_ftp_status)
    ftp_enable = ftp_sub.add_parser("enable", help="Enable FTP upload")
    ftp_enable.set_defaults(func=_cmd_ftp_set, action="enable")
    ftp_disable = ftp_sub.add_parser("disable", help="Disable FTP upload")
    ftp_disable.set_defaults(func=_cmd_ftp_set, action="disable")
    ftp_test = ftp_sub.add_parser("test", help="Test FTP connection")
    ftp_test.set_defaults(func=_cmd_ftp_test)

    # email
    email_parser = subparsers.add_parser("email", help="Email alerts")
    email_parser.set_defaults(func=_cmd_email_status)
    email_sub = email_parser.add_subparsers(dest="email_command")
    email_status = email_sub.add_parser("status", help="Show email alert status")
    email_status.set_defaults(func=_cmd_email_status)
    email_enable = email_sub.add_parser("enable", help="Enable email alerts")
    email_enable.set_defaults(func=_cmd_email_set, action="enable")
    email_disable = email_sub.add_parser("disable", help="Disable email alerts")
    email_disable.set_defaults(func=_cmd_email_set, action="disable")
    email_test = email_sub.add_parser("test", help="Test email delivery")
    email_test.set_defaults(func=_cmd_email_test)

    # recording toggle
    rec_parser = subparsers.add_parser("recording", help="Recording toggle")
    rec_sub = rec_parser.add_subparsers(dest="recording_command")
    rec_enable = rec_sub.add_parser("enable", help="Enable recording")
    rec_enable.set_defaults(func=_cmd_recording_set, action="enable")
    rec_disable = rec_sub.add_parser("disable", help="Disable recording")
    rec_disable.set_defaults(func=_cmd_recording_set, action="disable")
