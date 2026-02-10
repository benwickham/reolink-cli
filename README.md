# reolink-cli

A command-line interface for controlling Reolink cameras. Snapshots, streams, recordings, motion alerts, and full device management — from your terminal.

Human-friendly output by default. Machine-parseable `--json` mode for scripting and AI agent integration.

## Install

```bash
pip install reolink-cli
```

Or install from source:

```bash
git clone https://github.com/benwickham/reolink-cli.git
cd reolink-cli
pip install -e .
```

**Requirements:** Python 3.10+

## Quick Start

```bash
# Set your camera credentials (or pass --host / --password each time)
export REOLINK_HOST=192.168.1.100
export REOLINK_PASS=your_password

reolink info              # Device info
reolink battery           # Battery status
reolink snap              # Capture a snapshot
reolink stream            # Get RTSP stream URL
reolink watch --json      # Live event stream as JSONL
```

## Configuration

Credentials can be set via environment variables or CLI flags. Flags take precedence.

| Environment Variable | CLI Flag     | Default | Description            |
|---------------------|-------------|---------|------------------------|
| `REOLINK_HOST`      | `--host`    | —       | Camera IP or hostname  |
| `REOLINK_USER`      | `--user`    | `admin` | Username               |
| `REOLINK_PASS`      | `--password`| —       | Password               |
| `REOLINK_CHANNEL`   | `--channel` | `0`     | Channel index          |

Global flags:
- `--json` — Output as JSON (for scripting)
- `--quiet` — Suppress informational output
- `--timeout SEC` — Request timeout in seconds (default: 10)

## Commands

### Device Info

```bash
reolink info                # Model, firmware, serial, etc.
reolink battery             # Battery %, charging state, temperature
reolink storage             # SD card capacity, usage, health
reolink network             # IP, MAC, WiFi signal, ports
reolink time                # System time, timezone, NTP
reolink capabilities        # Full capability dump (JSON)
```

### Snapshots & Streams

```bash
reolink snap                          # Save snapshot as snapshot_<timestamp>.jpg
reolink snap --out photo.jpg          # Save to specific file
reolink snap --stream sub             # Use sub-stream (lower resolution)

reolink stream                        # Print RTSP URL
reolink stream --format rtmp          # Print RTMP URL
reolink stream --stream sub           # Sub-stream URL
reolink stream --open                 # Open in ffplay/vlc/mpv
```

### Recordings

```bash
reolink recordings list                       # Today's recordings
reolink recordings list --from yesterday      # Yesterday's recordings
reolink recordings list --from 2026-02-01     # Specific date
reolink recordings list --from 2026-02-01 --to 2026-02-10  # Date range

reolink recordings download /path/to/clip.mp4           # Download a clip
reolink recordings download /path/to/clip.mp4 -o out.mp4  # Custom output path

reolink recordings status             # Recording config (schedule, overwrite)
```

### Live Event Watcher

Poll for motion and AI detection events in real time:

```bash
reolink watch                         # Watch all events
reolink watch --json                  # JSONL output (one JSON object per line)
reolink watch --filter person vehicle # Only person and vehicle events
reolink watch --interval 5            # Poll every 5 seconds
reolink watch --exec "notify-send '{type} {action}'"  # Run command on event
```

Events are deduplicated — only state changes (start/stop) are emitted.

### Motion Detection

```bash
reolink motion                  # Show motion detection status
reolink motion enable           # Enable motion detection
reolink motion disable          # Disable motion detection
reolink motion sensitivity 75   # Set sensitivity (0-100)
```

### AI Detection

```bash
reolink ai                     # Show AI detection status
reolink ai enable people       # Enable person detection
reolink ai disable vehicle     # Disable vehicle detection
reolink ai enable dog_cat      # Enable animal detection
```

### Lights

```bash
reolink ir                     # Show IR light status
reolink ir set Auto            # Set IR to Auto/On/Off

reolink spotlight               # Show spotlight status
reolink spotlight on            # Turn spotlight on
reolink spotlight off           # Turn spotlight off
reolink spotlight set --brightness 50 --mode night

reolink status-led              # Show status LED state
reolink status-led on           # Turn LED on
reolink status-led off          # Turn LED off
```

### Image & Encoding

```bash
reolink image                  # Show image settings
reolink image set --brightness 150 --contrast 128
reolink image set --flip       # Flip image 180 degrees
reolink image set --mirror     # Mirror image

reolink encoding               # Show encoding settings
reolink encoding set --bitrate 2048 --framerate 30
reolink encoding set --stream sub --bitrate 512
```

### Audio

```bash
reolink audio                  # Show audio config
reolink audio set --mic-volume 50 --speaker-volume 80
reolink audio set --recording on
```

### Notifications & Alerts

```bash
reolink siren trigger              # Trigger the siren
reolink siren trigger --duration 5 # Trigger for 5 seconds
reolink siren stop                 # Stop the siren

reolink push                   # Show push notification status
reolink push enable            # Enable push notifications
reolink push disable           # Disable push notifications

reolink email                  # Show email alert status
reolink email enable           # Enable email alerts
reolink email test             # Send test email

reolink ftp                    # Show FTP upload status
reolink ftp enable             # Enable FTP upload
reolink ftp test               # Test FTP connection

reolink recording enable       # Enable recording
reolink recording disable      # Disable recording
```

### System Administration

```bash
reolink reboot --force         # Reboot the camera

reolink firmware               # Show firmware info
reolink firmware check         # Check for updates
reolink firmware update --force # Start firmware update

reolink ntp                    # Show NTP config
reolink ntp set --server pool.ntp.org

reolink time set 2026-02-10T14:30:00  # Set system time

reolink users                  # List users
reolink users add viewer pass123 --level guest
reolink users delete viewer --force
```

## JSON Mode

Every command supports `--json` for machine-parseable output:

```bash
reolink info --json
reolink battery --json | jq .batteryPercent
reolink watch --json | while read -r line; do echo "$line" | jq .; done
```

The `watch` command outputs JSONL (one JSON object per line) in `--json` mode, suitable for piping:

```json
{"type": "person", "action": "start", "timestamp": "2026-02-10T14:30:00"}
{"type": "person", "action": "stop", "timestamp": "2026-02-10T14:30:15"}
{"type": "motion", "action": "start", "timestamp": "2026-02-10T14:31:00"}
```

## Exit Codes

| Code | Meaning                |
|------|------------------------|
| 0    | Success                |
| 1    | Generic failure        |
| 2    | Invalid usage          |
| 3    | Authentication failure |
| 4    | Camera unreachable     |
| 5    | Feature not supported  |

## Shell Completion

### Bash

```bash
eval "$(register-python-argcomplete reolink 2>/dev/null)" || \
  complete -o default -C 'reolink --help' reolink
```

### Zsh

```zsh
# Add to ~/.zshrc
autoload -U bashcompinit && bashcompinit
eval "$(register-python-argcomplete reolink 2>/dev/null)" || true
```

## Supported Cameras

Tested with:
- Reolink Argus 4 Pro

Should work with any Reolink camera that supports the HTTP API, including:
- Argus series (Argus 3 Pro, Argus 4 Pro, Argus Eco, etc.)
- RLC series (RLC-810A, RLC-520A, etc.)
- E1 series (E1 Zoom, E1 Outdoor, etc.)
- Doorbell models
- NVR systems (via individual channel)

PTZ commands work on PTZ-capable cameras. Fixed cameras will return exit code 5 for unsupported PTZ features.

## Development

```bash
git clone https://github.com/benwickham/reolink-cli.git
cd reolink-cli
pip install -e .
pytest
```

## License

MIT
