# reolink-cli

A command-line interface for controlling Reolink cameras. Snapshots, streams, recordings, motion alerts, and full device management — from your terminal.

## Install

```bash
pip install reolink-cli
```

## Quick Start

```bash
export REOLINK_HOST=192.168.1.100
export REOLINK_PASS=your_password

reolink info              # Device info
reolink battery           # Battery status
reolink snap              # Capture a snapshot
reolink stream            # Get RTSP stream URL
reolink recordings list   # List recorded clips
reolink watch             # Live event stream
```

## Usage

See `reolink --help` for full command reference.

## License

MIT
