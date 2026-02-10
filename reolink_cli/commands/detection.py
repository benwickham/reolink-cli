"""Motion and AI detection status commands."""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

from reolink_cli.client import UnsupportedError
from reolink_cli.output import output

if TYPE_CHECKING:
    from reolink_cli.client import ReolinkClient

_ALARM_STATE = {0: "Idle", 1: "Triggered"}


def _cmd_motion_status(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Show motion detection status."""
    alarm = client.get_md_alarm()
    state = client.get_md_state()

    if args.json:
        output({"alarm": alarm, "state": state}, json_mode=True)
        return

    display: dict[str, str] = {}
    if "enable" in alarm:
        display["Enabled"] = "Yes" if alarm["enable"] == 1 else "No"

    # Current trigger state
    triggered = state.get("state", 0)
    display["Motion"] = _ALARM_STATE.get(triggered, str(triggered))

    # Sensitivity — may be a list (one per area) or a single value
    sens = alarm.get("sens")
    if isinstance(sens, list) and sens:
        # Show first area's sensitivity, or summarize
        values = [s.get("val", s) if isinstance(s, dict) else s for s in sens]
        display["Sensitivity"] = ", ".join(str(v) for v in values)
    elif sens is not None:
        display["Sensitivity"] = str(sens)

    output(display, title="Motion Detection")


def _cmd_ai_status(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Show AI detection status."""
    state = client.get_ai_state()

    # AI config is optional — some cameras only support GetAiState
    cfg = None
    try:
        cfg = client.get_ai_cfg()
    except UnsupportedError:
        pass

    if args.json:
        data: dict = {"state": state}
        if cfg is not None:
            data["config"] = cfg
        output(data, json_mode=True)
        return

    display: dict[str, str] = {}

    # AI detection types and their states
    ai_types = {
        "people": "Person",
        "vehicle": "Vehicle",
        "dog_cat": "Animal",
        "face": "Face",
    }
    for key, label in ai_types.items():
        info = state.get(key)
        if info is None:
            continue
        if isinstance(info, dict):
            supported = info.get("support", 0)
            if not supported:
                continue
            alarm = info.get("alarm_state", 0)
            status = _ALARM_STATE.get(alarm, str(alarm))
            # Include config if available
            if cfg and key in cfg:
                enabled = "On" if cfg[key] == 1 else "Off"
                display[label] = f"{enabled} ({status})"
            else:
                display[label] = status

    output(display, title="AI Detection")


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register detection commands with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    # motion command group — default to status
    motion_parser = subparsers.add_parser("motion", help="Motion detection")
    motion_parser.set_defaults(func=_cmd_motion_status)
    motion_sub = motion_parser.add_subparsers(dest="motion_command")
    motion_status = motion_sub.add_parser("status", help="Show motion detection status")
    motion_status.set_defaults(func=_cmd_motion_status)

    # ai command group — default to status
    ai_parser = subparsers.add_parser("ai", help="AI detection")
    ai_parser.set_defaults(func=_cmd_ai_status)
    ai_sub = ai_parser.add_subparsers(dest="ai_command")
    ai_status = ai_sub.add_parser("status", help="Show AI detection status")
    ai_status.set_defaults(func=_cmd_ai_status)
