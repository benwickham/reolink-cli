"""Light, image, encoding, and audio status and setter commands."""

from __future__ import annotations

import argparse
import sys
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


# ---------------------------------------------------------------------------
# Setter commands (Phase 4)
# ---------------------------------------------------------------------------

def _cmd_ir_set(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Set infrared lights state."""
    client.set_ir_lights(args.state)
    if args.json:
        output({"ir_lights": args.state}, json_mode=True)
    else:
        print(f"IR lights set to {args.state}.")


def _cmd_spotlight_set(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Set spotlight configuration."""
    kwargs: dict = {}
    if args.state is not None:
        kwargs["state"] = 1 if args.state == "on" else 0
    if getattr(args, "brightness", None) is not None:
        kwargs["brightness"] = args.brightness
    if getattr(args, "mode", None) is not None:
        mode_map = {"off": 0, "night": 1, "schedule": 3}
        kwargs["mode"] = mode_map.get(args.mode, 0)
    client.set_white_led(**kwargs)
    if args.json:
        output(kwargs, json_mode=True)
    else:
        print("Spotlight updated.")


def _cmd_status_led_set(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Set status LED state."""
    state = 1 if args.state == "on" else 0
    client.set_power_led(state)
    if args.json:
        output({"status_led": args.state}, json_mode=True)
    else:
        print(f"Status LED set to {args.state}.")


def _cmd_image_set(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Set image settings."""
    image_kwargs: dict = {}
    isp_kwargs: dict = {}

    if getattr(args, "brightness", None) is not None:
        image_kwargs["bright"] = args.brightness
    if getattr(args, "contrast", None) is not None:
        image_kwargs["contrast"] = args.contrast
    if getattr(args, "saturation", None) is not None:
        image_kwargs["saturation"] = args.saturation
    if getattr(args, "sharpness", None) is not None:
        image_kwargs["sharpe"] = args.sharpness
    if getattr(args, "flip", None) is not None:
        isp_kwargs["rotation"] = 180 if args.flip else 0
    if getattr(args, "mirror", None) is not None:
        isp_kwargs["mirroring"] = 1 if args.mirror else 0

    if image_kwargs:
        client.set_image(**image_kwargs)
    if isp_kwargs:
        client.set_isp(**isp_kwargs)
    if args.json:
        output({**image_kwargs, **isp_kwargs}, json_mode=True)
    else:
        print("Image settings updated.")


def _cmd_encoding_set(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Set encoding configuration."""
    stream = getattr(args, "stream", "main") or "main"
    kwargs: dict = {}
    if getattr(args, "bitrate", None) is not None:
        kwargs["bitRate"] = args.bitrate
    if getattr(args, "framerate", None) is not None:
        kwargs["frameRate"] = args.framerate
    if getattr(args, "resolution", None) is not None:
        kwargs["size"] = args.resolution
    client.set_enc(stream=stream, **kwargs)
    if args.json:
        output({"stream": stream, **kwargs}, json_mode=True)
    else:
        print(f"Encoding ({stream}) updated.")


def _cmd_audio_set(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Set audio configuration."""
    kwargs: dict = {}
    if getattr(args, "mic_volume", None) is not None:
        kwargs["micVolume"] = args.mic_volume
    if getattr(args, "speaker_volume", None) is not None:
        kwargs["speakerVolume"] = args.speaker_volume
    if getattr(args, "recording", None) is not None:
        kwargs["recordEnable"] = 1 if args.recording == "on" else 0
    client.set_audio_cfg(**kwargs)
    if args.json:
        output(kwargs, json_mode=True)
    else:
        print("Audio settings updated.")


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register controls status and setter commands with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    # ir command group — default to status
    ir_parser = subparsers.add_parser("ir", help="Infrared lights")
    ir_parser.set_defaults(func=_cmd_ir_status)
    ir_sub = ir_parser.add_subparsers(dest="ir_command")
    ir_status = ir_sub.add_parser("status", help="Show IR light status")
    ir_status.set_defaults(func=_cmd_ir_status)
    ir_set = ir_sub.add_parser("set", help="Set IR lights state")
    ir_set.add_argument("state", choices=["Auto", "On", "Off"], help="IR light state")
    ir_set.set_defaults(func=_cmd_ir_set)

    # spotlight command group — default to status
    spot_parser = subparsers.add_parser("spotlight", help="White LED spotlight")
    spot_parser.set_defaults(func=_cmd_spotlight_status)
    spot_sub = spot_parser.add_subparsers(dest="spotlight_command")
    spot_status = spot_sub.add_parser("status", help="Show spotlight status")
    spot_status.set_defaults(func=_cmd_spotlight_status)
    spot_set = spot_sub.add_parser("set", help="Set spotlight configuration")
    spot_set.add_argument("--state", choices=["on", "off"], help="Spotlight on/off")
    spot_set.add_argument("--brightness", type=int, metavar="N", help="Brightness (0-100)")
    spot_set.add_argument("--mode", choices=["off", "night", "schedule"], help="Spotlight mode")
    spot_set.set_defaults(func=_cmd_spotlight_set)
    spot_on = spot_sub.add_parser("on", help="Turn spotlight on")
    spot_on.set_defaults(func=_cmd_spotlight_set, state="on", brightness=None, mode=None)
    spot_off = spot_sub.add_parser("off", help="Turn spotlight off")
    spot_off.set_defaults(func=_cmd_spotlight_set, state="off", brightness=None, mode=None)

    # status-led command group
    led_parser = subparsers.add_parser("status-led", help="Power/status LED")
    led_parser.set_defaults(func=_cmd_status_led)
    led_sub = led_parser.add_subparsers(dest="led_command")
    led_on = led_sub.add_parser("on", help="Turn status LED on")
    led_on.set_defaults(func=_cmd_status_led_set, state="on")
    led_off = led_sub.add_parser("off", help="Turn status LED off")
    led_off.set_defaults(func=_cmd_status_led_set, state="off")

    # image command group — default to status
    image_parser = subparsers.add_parser("image", help="Image settings")
    image_parser.set_defaults(func=_cmd_image_status)
    image_sub = image_parser.add_subparsers(dest="image_command")
    image_status = image_sub.add_parser("status", help="Show image settings")
    image_status.set_defaults(func=_cmd_image_status)
    image_set = image_sub.add_parser("set", help="Set image settings")
    image_set.add_argument("--brightness", type=int, metavar="N", help="Brightness (0-255)")
    image_set.add_argument("--contrast", type=int, metavar="N", help="Contrast (0-255)")
    image_set.add_argument("--saturation", type=int, metavar="N", help="Saturation (0-255)")
    image_set.add_argument("--sharpness", type=int, metavar="N", help="Sharpness (0-255)")
    image_set.add_argument("--flip", action="store_true", default=None, help="Flip image 180")
    image_set.add_argument("--no-flip", dest="flip", action="store_false", help="Disable flip")
    image_set.add_argument("--mirror", action="store_true", default=None, help="Mirror image")
    image_set.add_argument("--no-mirror", dest="mirror", action="store_false", help="Disable mirror")
    image_set.set_defaults(func=_cmd_image_set)

    # encoding command group — default to status
    enc_parser = subparsers.add_parser("encoding", help="Video encoding settings")
    enc_parser.set_defaults(func=_cmd_encoding_status)
    enc_sub = enc_parser.add_subparsers(dest="encoding_command")
    enc_status = enc_sub.add_parser("status", help="Show encoding settings")
    enc_status.set_defaults(func=_cmd_encoding_status)
    enc_set = enc_sub.add_parser("set", help="Set encoding settings")
    enc_set.add_argument(
        "--stream", choices=["main", "sub"], default="main", help="Stream (default: main)",
    )
    enc_set.add_argument("--bitrate", type=int, metavar="N", help="Bitrate in kbps")
    enc_set.add_argument("--framerate", type=int, metavar="N", help="Frame rate in fps")
    enc_set.add_argument("--resolution", metavar="WxH", help="Resolution (e.g. 3840*2160)")
    enc_set.set_defaults(func=_cmd_encoding_set)

    # audio command group — default to status
    audio_parser = subparsers.add_parser("audio", help="Audio settings")
    audio_parser.set_defaults(func=_cmd_audio_status)
    audio_sub = audio_parser.add_subparsers(dest="audio_command")
    audio_status = audio_sub.add_parser("status", help="Show audio settings")
    audio_status.set_defaults(func=_cmd_audio_status)
    audio_set = audio_sub.add_parser("set", help="Set audio settings")
    audio_set.add_argument("--mic-volume", type=int, metavar="N", help="Mic volume (0-100)")
    audio_set.add_argument("--speaker-volume", type=int, metavar="N", help="Speaker volume (0-100)")
    audio_set.add_argument("--recording", choices=["on", "off"], help="Audio recording on/off")
    audio_set.set_defaults(func=_cmd_audio_set)
