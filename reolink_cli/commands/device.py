"""Device information and status commands."""

from __future__ import annotations

import argparse
import json
from typing import TYPE_CHECKING

from reolink_cli.client import UnsupportedError
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

_BATTERY_FIELDS = {
    "batteryPercent": "Battery",
    "chargeStatus": "Charging",
    "temperature": "Temperature",
    "lowPower": "Low Power",
    "sleepState": "Sleep State",
    "adapterStatus": "Adapter",
}

_CHARGE_STATUS = {0: "Not Charging", 1: "Charging"}
_SLEEP_STATE = {0: "Awake", 1: "Sleeping", 2: "Deep Sleep"}
_ADAPTER_STATUS = {0: "Disconnected", 1: "Connected"}


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


def _cmd_battery(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Show battery status."""
    raw = client.get_battery_info()

    if args.json:
        output(raw, json_mode=True)
        return

    display: dict[str, str] = {}
    for key, label in _BATTERY_FIELDS.items():
        if key not in raw:
            continue
        val = raw[key]
        if key == "batteryPercent":
            display[label] = f"{val}%"
        elif key == "chargeStatus":
            display[label] = _CHARGE_STATUS.get(val, str(val))
        elif key == "temperature":
            display[label] = f"{val}°C"
        elif key == "sleepState":
            display[label] = _SLEEP_STATE.get(val, str(val))
        elif key == "adapterStatus":
            display[label] = _ADAPTER_STATUS.get(val, str(val))
        else:
            display[label] = str(val)
    output(display, title="Battery Status")


def _cmd_storage(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Show storage information."""
    raw = client.get_hdd_info()

    if args.json:
        output(raw, json_mode=True)
        return

    if not raw:
        output({"Status": "No storage devices found"}, title="Storage")
        return

    for i, disk in enumerate(raw):
        title = f"Storage (Disk {i})" if len(raw) > 1 else "Storage"
        display: dict[str, str] = {}
        if "capacity" in disk:
            display["Capacity"] = f"{disk['capacity']} GB"
        if "mount" in disk:
            display["Mounted"] = "Yes" if disk["mount"] == 1 else "No"
        if "size" in disk:
            display["Total Size"] = f"{disk['size']} GB"
        if "used" in disk:
            display["Used"] = f"{disk['used']} GB"
        if "free" in disk:
            display["Free"] = f"{disk['free']} GB"
        if "storageType" in disk:
            display["Type"] = disk["storageType"]
        if "overWrite" in disk:
            display["Overwrite"] = "Enabled" if disk["overWrite"] == 1 else "Disabled"
        if "health" in disk:
            display["Health"] = disk["health"]
        if "id" in disk:
            display["ID"] = str(disk["id"])
        output(display, title=title)
        if i < len(raw) - 1:
            print()


def _cmd_network(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Show network information."""
    link = client.get_local_link()
    ports = client.get_net_port()

    # WiFi signal is optional — may not be supported on wired cameras
    wifi_signal = None
    try:
        wifi_signal = client.get_wifi_signal()
    except UnsupportedError:
        pass

    if args.json:
        data: dict = {"localLink": link, "ports": ports}
        if wifi_signal is not None:
            data["wifiSignal"] = wifi_signal
        output(data, json_mode=True)
        return

    display: dict[str, str] = {}
    if "activeLink" in link:
        display["Connection"] = link["activeLink"]
    if "mac" in link:
        display["MAC"] = link["mac"]
    if "type" in link:
        display["IP Mode"] = link["type"]

    # Extract IP from static or DHCP config
    static = link.get("static", {})
    dns = link.get("dns", {})
    if static.get("ip"):
        display["IP"] = static["ip"]
    if static.get("mask"):
        display["Subnet"] = static["mask"]
    if static.get("gateway"):
        display["Gateway"] = static["gateway"]
    if dns.get("dns1"):
        display["DNS 1"] = dns["dns1"]
    if dns.get("dns2"):
        display["DNS 2"] = dns["dns2"]

    if wifi_signal is not None:
        display["WiFi Signal"] = f"{wifi_signal} dBm"

    # Ports
    port_fields = {
        "httpPort": "HTTP Port",
        "httpsPort": "HTTPS Port",
        "rtspPort": "RTSP Port",
        "rtmpPort": "RTMP Port",
        "onvifPort": "ONVIF Port",
        "mediaPort": "Media Port",
    }
    for key, label in port_fields.items():
        if key in ports:
            display[label] = str(ports[key])

    output(display, title="Network")


def _cmd_time(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Show system time."""
    raw = client.get_time()

    if args.json:
        output(raw, json_mode=True)
        return

    time_info = raw.get("Time", raw)
    dst_info = raw.get("Dst", {})

    display: dict[str, str] = {}
    # Format datetime
    year = time_info.get("year", "")
    mon = time_info.get("mon", "")
    day = time_info.get("day", "")
    hour = time_info.get("hour", "")
    minute = time_info.get("min", "")
    sec = time_info.get("sec", "")
    if year:
        display["Time"] = f"{year}-{mon:02d}-{day:02d} {hour:02d}:{minute:02d}:{sec:02d}"
    if "timeZone" in time_info:
        # Timezone offset in seconds, convert to hours
        tz_sec = time_info["timeZone"]
        tz_hours = tz_sec // 3600
        sign = "+" if tz_hours >= 0 else ""
        display["Timezone"] = f"UTC{sign}{tz_hours}"
    if "hourFmt" in time_info:
        display["Hour Format"] = "12h" if time_info["hourFmt"] == 1 else "24h"
    if "timeFmt" in time_info:
        display["Date Format"] = time_info["timeFmt"]
    if dst_info.get("enable") is not None:
        display["DST"] = "Enabled" if dst_info["enable"] == 1 else "Disabled"

    output(display, title="System Time")


def _cmd_capabilities(args: argparse.Namespace, client: ReolinkClient) -> None:
    """Show camera capabilities."""
    raw = client.get_ability()
    # Capabilities are always JSON — too complex for human format
    print(json.dumps(raw, indent=2))


def register(subparsers: argparse._SubParsersAction) -> None:
    """Register device commands with the argument parser.

    Args:
        subparsers: The subparsers action from the parent parser.
    """
    info_parser = subparsers.add_parser("info", help="Show device information")
    info_parser.set_defaults(func=_cmd_info)

    battery_parser = subparsers.add_parser("battery", help="Show battery status")
    battery_parser.set_defaults(func=_cmd_battery)

    storage_parser = subparsers.add_parser("storage", help="Show storage information")
    storage_parser.set_defaults(func=_cmd_storage)

    network_parser = subparsers.add_parser("network", help="Show network information")
    network_parser.set_defaults(func=_cmd_network)

    time_parser = subparsers.add_parser("time", help="System time")
    time_parser.set_defaults(func=_cmd_time)

    capabilities_parser = subparsers.add_parser(
        "capabilities", help="Show camera capabilities (JSON)",
    )
    capabilities_parser.set_defaults(func=_cmd_capabilities)
