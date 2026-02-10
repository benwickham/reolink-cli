"""Light, image, encoding, and audio status commands."""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

from reolink_cli.output import output

if TYPE_CHECKING:
    from reolink_cli.client import ReolinkClient

_IR_STATE = {"Auto": "Auto", "Off": "Off", "On": "On"}
_WL_MODE = {0: "Off", 1: "Night Mode", 3: "Schedule"}


def _cmd_ir_status(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Show infrared lights status."""
    raw = client.get_ir_lights()

    if args.json:
        output(raw, json_mode=True)
        return

    display: dict[str, str] = {}
    state = raw.get("state", "")
    display["State"] = _IR_STATE.get(state, str(state))
    output(display, title="IR Lights")


def _cmd_spotlight_status(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Show spotlight (white LED) status."""
    raw = client.get_white_led()

    if args.json:
        output(raw, json_mode=True)
        return

    display: dict[str, str] = {}
    if "state" in raw:
        display["State"] = "On" if raw["state"] == 1 else "Off"
    if "mode" in raw:
        display["Mode"] = _WL_MODE.get(raw["mode"], str(raw["mode"]))
    if "bright" in raw:
        display["Brightness"] = f"{raw['bright']}%"
    if "LightingSchedule" in raw:
        sched = raw["LightingSchedule"]
        start = sched.get("StartHour", {})
        end = sched.get("EndHour", {})
        if start and end:
            display["Schedule"] = (
                f"{start.get('hour', 0):02d}:{start.get('min', 0):02d} - "
                f"{end.get('hour', 0):02d}:{end.get('min', 0):02d}"
            )

    output(display, title="Spotlight")


def _cmd_status_led(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Show power/status LED state."""
    raw = client.get_power_led()

    if args.json:
        output(raw, json_mode=True)
        return

    display: dict[str, str] = {}
    if "state" in raw:
        display["State"] = "On" if raw["state"] == 1 else "Off"
    output(display, title="Status LED")


def _cmd_image_status(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Show image settings."""
    image = client.get_image()
    isp = client.get_isp()

    if args.json:
        output({"image": image, "isp": isp}, json_mode=True)
        return

    display: dict[str, str] = {}
    image_fields = {
        "bright": "Brightness",
        "contrast": "Contrast",
        "saturation": "Saturation",
        "sharpe": "Sharpness",
        "hue": "Hue",
    }
    for key, label in image_fields.items():
        if key in image:
            display[label] = str(image[key])

    isp_fields = {
        "dayNight": "Day/Night",
        "antiFlicker": "Anti-Flicker",
        "exposure": "Exposure",
        "whiteBalance": "White Balance",
    }
    for key, label in isp_fields.items():
        if key in isp:
            display[label] = str(isp[key])

    # Boolean ISP flags
    if "hdr" in isp:
        display["HDR"] = "On" if isp["hdr"] == 1 else "Off"
    if "rotation" in isp:
        display["Rotation"] = f"{isp['rotation']}°" if isp["rotation"] else "None"
    if "mirroring" in isp:
        display["Mirror"] = "On" if isp["mirroring"] == 1 else "Off"

    output(display, title="Image Settings")


def _fmt_stream(stream: dict, prefix: str) -> dict[str, str]:
    """Format a stream config dict into display fields.

    Args:
        stream: Stream configuration dict.
        prefix: Label prefix (e.g. "Main" or "Sub").

    Returns:
        Dict of display label -> value pairs.
    """
    display: dict[str, str] = {}
    if "size" in stream:
        display[f"{prefix} Resolution"] = stream["size"]
    if "bitRate" in stream:
        display[f"{prefix} Bitrate"] = f"{stream['bitRate']} kbps"
    if "frameRate" in stream:
        display[f"{prefix} Frame Rate"] = f"{stream['frameRate']} fps"

    # Codec may be nested
    video = stream.get("video", {})
    codec = video.get("codec") if isinstance(video, dict) else None
    if codec:
        display[f"{prefix} Codec"] = codec
    elif "vType" in stream:
        display[f"{prefix} Codec"] = stream["vType"]

    if "profile" in stream:
        display[f"{prefix} Profile"] = stream["profile"]
    return display


def _cmd_encoding_status(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Show encoding configuration."""
    raw = client.get_enc()

    if args.json:
        output(raw, json_mode=True)
        return

    display: dict[str, str] = {}
    main = raw.get("mainStream", {})
    sub = raw.get("subStream", {})
    display.update(_fmt_stream(main, "Main"))
    display.update(_fmt_stream(sub, "Sub"))
    output(display, title="Encoding")


def _cmd_audio_status(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Show audio configuration and alarm status."""
    cfg = client.get_audio_cfg()
    alarm = client.get_audio_alarm()

    if args.json:
        output({"config": cfg, "alarm": alarm}, json_mode=True)
        return

    display: dict[str, str] = {}
    if "micVolume" in cfg:
        display["Mic Volume"] = str(cfg["micVolume"])
    if "speakerVolume" in cfg:
        display["Speaker Volume"] = str(cfg["speakerVolume"])
    if "recordEnable" in cfg:
        display["Recording"] = "On" if cfg["recordEnable"] == 1 else "Off"
    if "enable" in alarm:
        display["Audio Alarm"] = "Enabled" if alarm["enable"] == 1 else "Disabled"

    output(display, title="Audio")


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register controls status commands with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    # ir command group — default to status
    ir_parser = subparsers.add_parser("ir", help="Infrared lights")
    ir_parser.set_defaults(func=_cmd_ir_status)
    ir_sub = ir_parser.add_subparsers(dest="ir_command")
    ir_status = ir_sub.add_parser("status", help="Show IR light status")
    ir_status.set_defaults(func=_cmd_ir_status)

    # spotlight command group — default to status
    spot_parser = subparsers.add_parser("spotlight", help="White LED spotlight")
    spot_parser.set_defaults(func=_cmd_spotlight_status)
    spot_sub = spot_parser.add_subparsers(dest="spotlight_command")
    spot_status = spot_sub.add_parser("status", help="Show spotlight status")
    spot_status.set_defaults(func=_cmd_spotlight_status)

    # status-led — standalone read command
    led_parser = subparsers.add_parser("status-led", help="Power/status LED")
    led_parser.set_defaults(func=_cmd_status_led)

    # image command group — default to status
    image_parser = subparsers.add_parser("image", help="Image settings")
    image_parser.set_defaults(func=_cmd_image_status)
    image_sub = image_parser.add_subparsers(dest="image_command")
    image_status = image_sub.add_parser("status", help="Show image settings")
    image_status.set_defaults(func=_cmd_image_status)

    # encoding command group — default to status
    enc_parser = subparsers.add_parser("encoding", help="Video encoding settings")
    enc_parser.set_defaults(func=_cmd_encoding_status)
    enc_sub = enc_parser.add_subparsers(dest="encoding_command")
    enc_status = enc_sub.add_parser("status", help="Show encoding settings")
    enc_status.set_defaults(func=_cmd_encoding_status)

    # audio command group — default to status
    audio_parser = subparsers.add_parser("audio", help="Audio settings")
    audio_parser.set_defaults(func=_cmd_audio_status)
    audio_sub = audio_parser.add_subparsers(dest="audio_command")
    audio_status = audio_sub.add_parser("status", help="Show audio settings")
    audio_status.set_defaults(func=_cmd_audio_status)
