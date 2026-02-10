"""Snapshot, stream, recordings, and live event watcher commands."""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from reolink_cli.output import format_json, output, print_error

if TYPE_CHECKING:
    from reolink_cli.client import ReolinkClient


def _cmd_snap(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Capture a JPEG snapshot and save to file."""
    stream = getattr(args, "stream", "main") or "main"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = getattr(args, "out", None) or f"snapshot_{timestamp}.jpg"

    data = client.snap(stream=stream)
    with open(out_path, "wb") as f:
        f.write(data)

    if args.json:
        output({"file": out_path, "size": len(data), "stream": stream}, json_mode=True)
    else:
        print(f"Saved snapshot to {out_path} ({len(data)} bytes)")


def _cmd_stream(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Get the RTSP or RTMP stream URL."""
    ports = client.get_net_port()
    fmt = getattr(args, "format", "rtsp") or "rtsp"
    stream = getattr(args, "stream", "main") or "main"

    stream_path = "h264Preview" if stream == "main" else "h264Preview_01"
    channel_str = f"{client.channel + 1:02d}"

    if fmt == "rtsp":
        port = ports.get("rtspPort", 554)
        url = (
            f"rtsp://{client.username}:{client.password}"
            f"@{client.host}:{port}//{stream_path}_{channel_str}_{stream}"
        )
    else:
        port = ports.get("rtmpPort", 1935)
        url = (
            f"rtmp://{client.host}:{port}/bcs/channel{client.channel}"
            f"_{stream}.bcs?channel={client.channel}"
            f"&stream=0&user={client.username}&password={client.password}"
        )

    if args.json:
        output({"url": url, "format": fmt, "stream": stream}, json_mode=True)
    else:
        print(url)

    if getattr(args, "open", False):
        for player in ["ffplay", "vlc", "mpv"]:
            try:
                subprocess.Popen(
                    [player, url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                if not args.json:
                    print(f"Opened in {player}")
                return
            except FileNotFoundError:
                continue
        print_error("No media player found (tried ffplay, vlc, mpv)")


def _parse_date(value: str) -> datetime:
    """Parse a date string, supporting 'today', 'yesterday', and ISO format.

    Args:
        value: Date string to parse.

    Returns:
        Parsed datetime.
    """
    if value == "today":
        return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if value == "yesterday":
        return (datetime.now() - timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        # Try date-only format
        return datetime.strptime(value, "%Y-%m-%d")


def _dt_to_api(dt: datetime) -> dict[str, int]:
    """Convert a datetime to the Reolink API time dict format.

    Args:
        dt: Datetime to convert.

    Returns:
        Dict with year, mon, day, hour, min, sec.
    """
    return {
        "year": dt.year,
        "mon": dt.month,
        "day": dt.day,
        "hour": dt.hour,
        "min": dt.minute,
        "sec": dt.second,
    }


def _cmd_recordings_list(args: argparse.Namespace, client: ReolinkClient) -> None:
    """List recordings in a date range."""
    from_str = getattr(args, "from", None) or getattr(args, "from_date", None) or "today"
    to_str = getattr(args, "to", None) or getattr(args, "to_date", None)

    start_dt = _parse_date(from_str)
    if to_str:
        end_dt = _parse_date(to_str)
    else:
        end_dt = start_dt.replace(hour=23, minute=59, second=59)

    files = client.search_recordings(
        start_time=_dt_to_api(start_dt),
        end_time=_dt_to_api(end_dt),
    )

    if args.json:
        output({"recordings": files, "count": len(files)}, json_mode=True)
        return

    if not files:
        print("No recordings found.")
        return

    print(f"Found {len(files)} recording(s):\n")
    for f in files:
        start = f.get("StartTime", {})
        end = f.get("EndTime", {})
        start_str = (
            f"{start.get('year', '')}-{start.get('mon', 0):02d}-{start.get('day', 0):02d} "
            f"{start.get('hour', 0):02d}:{start.get('min', 0):02d}:{start.get('sec', 0):02d}"
        )
        end_str = (
            f"{end.get('hour', 0):02d}:{end.get('min', 0):02d}:{end.get('sec', 0):02d}"
        )
        name = f.get("name", "unknown")
        size = f.get("size", 0)
        size_mb = size / (1024 * 1024) if size > 0 else 0
        rec_type = f.get("type", "")
        print(f"  {start_str} - {end_str}  {size_mb:6.1f} MB  {rec_type:8s}  {name}")


def _cmd_recordings_download(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Download a recording file."""
    filename = args.filename
    out_path = getattr(args, "out", None) or os.path.basename(filename)

    resp = client.download_file(filename)
    try:
        total = 0
        with open(out_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=65536):
                f.write(chunk)
                total += len(chunk)
                if not args.quiet and not args.json:
                    mb = total / (1024 * 1024)
                    print(f"\r  Downloaded {mb:.1f} MB", end="", flush=True)
        if not args.quiet and not args.json:
            print()
    finally:
        resp.close()

    if args.json:
        output({"file": out_path, "size": total}, json_mode=True)
    elif not args.quiet:
        mb = total / (1024 * 1024)
        print(f"Saved to {out_path} ({mb:.1f} MB)")


def _cmd_recordings_status(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Show recording configuration."""
    raw = client.get_rec()

    if args.json:
        output(raw, json_mode=True)
        return

    display: dict[str, str] = {}
    if "enable" in raw:
        display["Recording"] = "Enabled" if raw["enable"] == 1 else "Disabled"
    if "overwrite" in raw:
        display["Overwrite"] = "Enabled" if raw["overwrite"] == 1 else "Disabled"
    if "packDuration" in raw:
        display["Pack Duration"] = f"{raw['packDuration']}s"
    if "preRec" in raw:
        display["Pre-Record"] = "On" if raw["preRec"] == 1 else "Off"
    if "postRec" in raw:
        display["Post-Record"] = f"{raw['postRec']}s"
    if "schedule" in raw:
        display["Schedule"] = "Configured"

    output(display, title="Recording Config")


def _cmd_watch(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Live event poller — watch for motion and AI detection events."""
    interval = getattr(args, "interval", 3) or 3
    event_filter = getattr(args, "filter", None)
    exec_cmd = getattr(args, "exec", None) or getattr(args, "exec_cmd", None)

    # Track previous state for edge detection
    prev_state: dict[str, bool] = {}

    # Handle SIGINT gracefully
    running = True

    def _handle_sigint(signum: int, frame: Any) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, _handle_sigint)

    if not args.json and not args.quiet:
        print("Watching for events... (Ctrl+C to stop)\n")

    while running:
        try:
            ai_state = client.get_ai_state()
            md_state = client.get_md_state()
        except KeyboardInterrupt:
            break

        now = datetime.now()
        timestamp = now.isoformat()

        events: list[dict[str, Any]] = []

        # Check motion
        motion_triggered = md_state.get("state", 0) == 1
        if "motion" not in prev_state or prev_state["motion"] != motion_triggered:
            if event_filter is None or "motion" in event_filter:
                action = "start" if motion_triggered else "stop"
                events.append({
                    "type": "motion",
                    "action": action,
                    "timestamp": timestamp,
                })
            prev_state["motion"] = motion_triggered

        # Check AI detection types
        ai_types = {"people": "person", "vehicle": "vehicle", "dog_cat": "animal"}
        for api_key, event_type in ai_types.items():
            info = ai_state.get(api_key)
            if not isinstance(info, dict) or not info.get("support", 0):
                continue
            triggered = info.get("alarm_state", 0) == 1
            if api_key not in prev_state or prev_state[api_key] != triggered:
                if event_filter is None or event_type in event_filter:
                    action = "start" if triggered else "stop"
                    events.append({
                        "type": event_type,
                        "action": action,
                        "timestamp": timestamp,
                    })
                prev_state[api_key] = triggered

        # Emit events
        for event in events:
            if args.json:
                print(json.dumps(event), flush=True)
            elif not args.quiet:
                print(f"[{event['timestamp']}] {event['type']} {event['action']}")

            if exec_cmd:
                cmd = exec_cmd.replace("{type}", event["type"])
                cmd = cmd.replace("{timestamp}", event["timestamp"])
                cmd = cmd.replace("{action}", event["action"])
                try:
                    subprocess.Popen(cmd, shell=True)
                except OSError as exc:
                    print_error(f"Failed to run exec command: {exc}")

        try:
            time.sleep(interval)
        except KeyboardInterrupt:
            break

    if not args.json and not args.quiet:
        print("\nStopped watching.")


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register media commands with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    # snap
    snap_parser = subparsers.add_parser("snap", help="Capture a JPEG snapshot")
    snap_parser.add_argument("--out", "-o", metavar="FILE", help="Output file path")
    snap_parser.add_argument(
        "--stream", choices=["main", "sub"], default="main",
        help="Stream to capture from (default: main)",
    )
    snap_parser.set_defaults(func=_cmd_snap)

    # stream
    stream_parser = subparsers.add_parser("stream", help="Get stream URL")
    stream_parser.add_argument(
        "--format", "-f", choices=["rtsp", "rtmp"], default="rtsp",
        help="Stream format (default: rtsp)",
    )
    stream_parser.add_argument(
        "--stream", choices=["main", "sub"], default="main",
        help="Stream quality (default: main)",
    )
    stream_parser.add_argument(
        "--open", action="store_true", default=False,
        help="Open stream in a media player (ffplay/vlc/mpv)",
    )
    stream_parser.set_defaults(func=_cmd_stream)

    # recordings (command group)
    rec_parser = subparsers.add_parser("recordings", help="Recording management")
    rec_sub = rec_parser.add_subparsers(dest="recordings_command")

    # recordings list
    rec_list = rec_sub.add_parser("list", help="List recordings")
    rec_list.add_argument(
        "--from", dest="from_date", metavar="DATE", default="today",
        help="Start date (default: today). Accepts: today, yesterday, YYYY-MM-DD, ISO datetime",
    )
    rec_list.add_argument(
        "--to", dest="to_date", metavar="DATE",
        help="End date (default: end of start date)",
    )
    rec_list.set_defaults(func=_cmd_recordings_list)

    # recordings download
    rec_dl = rec_sub.add_parser("download", help="Download a recording")
    rec_dl.add_argument("filename", help="Recording filename (from 'recordings list')")
    rec_dl.add_argument("--out", "-o", metavar="FILE", help="Output file path")
    rec_dl.set_defaults(func=_cmd_recordings_download)

    # recordings status
    rec_status = rec_sub.add_parser("status", help="Show recording configuration")
    rec_status.set_defaults(func=_cmd_recordings_status)

    # Default for 'recordings' with no subcommand
    rec_parser.set_defaults(func=_cmd_recordings_status)

    # watch
    watch_parser = subparsers.add_parser("watch", help="Watch for live events")
    watch_parser.add_argument(
        "--interval", "-i", type=float, default=3,
        help="Poll interval in seconds (default: 3)",
    )
    watch_parser.add_argument(
        "--filter", nargs="+", metavar="TYPE",
        choices=["motion", "person", "vehicle", "animal"],
        help="Only show these event types",
    )
    watch_parser.add_argument(
        "--exec", dest="exec_cmd", metavar="CMD",
        help="Run command on each event (vars: {type}, {timestamp}, {action})",
    )
    watch_parser.set_defaults(func=_cmd_watch)
