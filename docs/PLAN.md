# Reolink CLI — Build Plan

**Goal:** Build a public, open-source Python CLI for controlling Reolink cameras. Human-friendly terminal tool and AI-agent scriptable.

**Repo:** `github.com/benwickham/reolink-cli`
**Local:** `~/Projects/reolink-cli/`
**Owner:** Ben Wickham
**Created:** 2026-02-10
**Status:** 🟡 Planning Complete — Ready to Build

---

## Engineering Workflow

- **OR-Bit** (me) handles orchestration: planning, repo setup, task prompts, review, testing
- **Claude Code** (`claude` CLI) handles implementation: writing code inside the repo
- Work is executed phase by phase — Claude Code gets a focused prompt per phase, I review before moving on
- All work happens in `~/Projects/reolink-cli/` — isolated from OpenClaw workspace

---

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Language | Python 3.14 | Widely available, fast to iterate |
| CLI framework | `argparse` (stdlib) | Zero deps, good enough for this scope |
| HTTP client | `requests` | Ubiquitous, simple sync API |
| Structure | Python package (`reolink_cli/`) with command modules | Proper open-source project structure |
| Config | env vars + optional config file | env vars for quick start, file for persistence |
| Output | Human-readable default, `--json` flag | Agent-friendly from day one, no colour |
| Packaging | `pyproject.toml` + pip installable | Modern Python standard, publishable to PyPI |
| Install | `pip install reolink-cli` (or `pip install -e .` for dev) | Standard Python install, no symlink hacks |
| Location | `~/Projects/reolink-cli/` | Standalone repo, separate from OpenClaw |
| Scope | CLI only | OpenClaw skill integration is a separate follow-up |

---

## Phase 0: Repo Setup
*Orchestrated by OR-Bit — not Claude Code*

- [x] **0.1** Create `~/Projects/` directory on orbitbox ✅
- [x] **0.2** Create `~/Projects/reolink-cli/` with initial structure ✅
- [x] **0.3** Initialize git repo ✅
- [x] **0.4** Create public GitHub repo `benwickham/reolink-cli` ✅
- [x] **0.5** Push initial commit (README, LICENSE, pyproject.toml, .gitignore, package skeleton) ✅

---

## Phase 1: Foundation
*Core plumbing — auth, config, transport, CLI skeleton*

- [ ] **1.1** Implement API client class (`ReolinkAPI`)
  - HTTP transport layer (POST to `/cgi-bin/api.cgi`)
  - Token-based auth (Login/Logout)
  - Auto-login on first call, token caching within session
  - Proper error handling (network errors, auth failures, API errors)
  - Timeout handling (default 10s, configurable)
  - JSON response parsing + error code mapping

- [ ] **1.3** Implement config loading
  - Env vars: `REOLINK_HOST`, `REOLINK_USER`, `REOLINK_PASS`, `REOLINK_CHANNEL`
  - CLI flag overrides: `--host`, `--user`, `--pass`, `--channel`
  - Precedence: flags > env > defaults
  - Validate required fields (host + pass minimum), clear error if missing

- [ ] **1.4** Implement CLI skeleton with argparse
  - Top-level parser with global flags (`--host`, `--user`, `--pass`, `--channel`, `--json`, `--quiet`, `--timeout`)
  - Subcommand routing via `add_subparsers`
  - `-h`/`--help` on every command
  - `--version` flag
  - Consistent output formatting (human vs JSON)
  - Exit codes: 0=success, 1=generic, 2=bad usage, 3=auth fail, 4=unreachable, 5=unsupported

- [ ] **1.5** Implement output formatter
  - Human mode: clean, plain text (no colour), tabular where appropriate
  - JSON mode: structured, stable keys, machine-parseable
  - Quiet mode: suppress non-essential output
  - stderr for errors/diagnostics, stdout for data

- [ ] **1.6** Verify basic execution
  - `pip install -e .` from repo root
  - Test: `reolink --help`, `reolink --version`

### Phase 1 Acceptance
```bash
reolink --help          # shows all subcommands
reolink --version       # prints version
reolink info            # connects to camera, shows device info
```

---

## Phase 2: Device & Read-Only Commands
*Everything that reads state without changing anything*

- [ ] **2.1** `reolink info` — Device info
  - API: `GetDevInfo`
  - Output: model, firmware, hardware version, serial, UID, channel count

- [ ] **2.2** `reolink battery` — Battery status
  - API: `GetBatteryInfo`
  - Output: percentage, temperature, charging state, sleep state

- [ ] **2.3** `reolink storage` — Storage info
  - API: `GetHddInfo`
  - Output: SD card capacity, used/free, overwrite enabled, health

- [ ] **2.4** `reolink network` — Network info
  - API: `GetLocalLink`, `GetNetPort`, `GetWifiSignal`
  - Output: IP, MAC, WiFi SSID, signal strength, RSSP/RTMP/ONVIF ports

- [ ] **2.5** `reolink time` — System time
  - API: `GetTime`
  - Output: current time, timezone, NTP status

- [ ] **2.6** `reolink capabilities` — Capability dump
  - API: `GetAbility`
  - Output: full capability JSON (always JSON, too complex for human format)

- [ ] **2.7** `reolink motion status` — Motion detection state
  - API: `GetMdAlarm`, `GetMdState`, `GetAlarm`
  - Output: enabled/disabled, current trigger state, sensitivity

- [ ] **2.8** `reolink ai status` — AI detection state
  - API: `GetAiState`, `GetAiCfg`
  - Output: per-type detection state (person/vehicle/animal), what's currently detected

- [ ] **2.9** `reolink ir status` / `reolink spotlight status` / `reolink status-led`
  - API: `GetIrLights`, `GetWhiteLed`, `GetPowerLed`
  - Output: on/off state, mode, brightness

- [ ] **2.10** `reolink image status` — Image settings
  - API: `GetImage`, `GetIsp`
  - Output: brightness, contrast, saturation, sharpness, hue, day/night mode, HDR, exposure

- [ ] **2.11** `reolink encoding status` — Encoding config
  - API: `GetEnc`
  - Output: bitrate, framerate, codec, resolution per stream (main/sub)

- [ ] **2.12** `reolink audio status` — Audio state
  - API: `GetAudioCfg`, `GetAudioAlarm`
  - Output: recording on/off, mic volume, speaker volume, audio alarm state

- [ ] **2.13** `reolink osd status` — OSD overlay
  - API: `GetOsd`
  - Output: name position, date position, watermark enabled

- [ ] **2.14** `reolink pir status` — PIR sensor (if supported)
  - API: `GetPirInfo`
  - Output: enabled, sensitivity, interval

- [ ] **2.15** `reolink users list` — User management (read)
  - API: `GetUser`, `GetOnline`
  - Output: user list, currently online sessions

### Phase 2 Acceptance
All read commands return clean output in both human and `--json` modes. Unsupported features (e.g. PTZ on a fixed camera) return exit code 5 with clear message.

---

## Phase 3: Snapshots, Streams & Recordings
*The high-value media commands*

- [ ] **3.1** `reolink snap` — Capture snapshot
  - API: `Snap` (GET `/cgi-bin/api.cgi?cmd=Snap&channel=0`)
  - Flags: `--out <file>` (default: `snapshot_<timestamp>.jpg`), `--stream main|sub`
  - Write JPEG to file, print path to stdout

- [ ] **3.2** `reolink stream` — Get stream URL
  - API: `GetNetPort` + `GetEnc` to construct URL
  - Flags: `--format rtsp|rtmp` (default: rtsp), `--stream main|sub`, `--codec h264|h265`
  - Output: full stream URL with credentials
  - Bonus: `--open` flag to launch in ffplay/VLC

- [ ] **3.3** `reolink recordings list` — List recordings
  - API: `Search`
  - Flags: `--from <datetime>`, `--to <datetime>` (default: today)
  - Output: filename, start time, end time, size, type (alarm/manual/schedule)

- [ ] **3.4** `reolink recordings download` — Download clip
  - API: `Download` / VOD source
  - Args: `<filename>`
  - Flags: `--out <path>` (default: original filename)
  - Progress bar for large downloads

- [ ] **3.5** `reolink recordings status` — Recording config
  - API: `GetRec` / `GetRecV20`
  - Output: recording enabled, schedule, overwrite status, packing time, post-record time

- [ ] **3.6** `reolink watch` — Live event poller
  - Polls `GetAiState` + `GetMdState` every 3-5 seconds
  - Outputs events as they happen (person detected, vehicle, motion start/stop)
  - Flags: `--interval <seconds>` (default: 3), `--filter person|vehicle|dog_cat|motion`
  - `--json` outputs one JSON object per line (JSONL) for piping
  - `--exec <command>` runs a shell command on each event (template vars: `{type}`, `{timestamp}`)
  - Runs until Ctrl+C, clean exit on SIGINT
  - No new dependencies — just a polling loop over existing API calls
  - Deduplicates: only emits on state *change* (rising/falling edge), not every poll

### Phase 3 Acceptance
```bash
reolink snap --out test.jpg       # saves JPEG
reolink stream                     # prints rtsp:// URL
reolink recordings list --from today  # lists today's clips
reolink watch --json               # streams events as JSONL
reolink watch --filter person      # only person events
```

---

## Phase 4: Controls & Setters
*Commands that change camera state*

- [ ] **4.1** Motion detection controls
  - `reolink motion enable|disable` → `SetMdAlarm`
  - `reolink motion sensitivity --value <n>` → `SetMdAlarm` sensitivity param

- [ ] **4.2** AI detection controls
  - `reolink ai sensitivity --type <t> --value <n>` → `SetAiCfg`
  - `reolink ai delay --type <t> --value <n>` → `SetAiCfg`

- [ ] **4.3** PIR controls
  - `reolink pir set --enable --sensitivity <n> --interval <n>` → `SetPirInfo` / similar

- [ ] **4.4** Light controls
  - `reolink ir enable|disable` → `SetIrLights`
  - `reolink spotlight on|off` → `SetWhiteLed`
  - `reolink spotlight set --brightness <n> --mode <m>` → `SetWhiteLed`
  - `reolink status-led on|off` → `SetPowerLed`

- [ ] **4.5** Siren & buzzer
  - `reolink siren on --duration <n>` → `SetSiren` (AudioAlarmPlay)
  - `reolink siren off` → stop siren
  - `reolink buzzer enable|disable` → `SetBuzzerAlarmV20`

- [ ] **4.6** Audio controls
  - `reolink audio enable|disable` → `SetAudioCfg`
  - `reolink audio volume --value <n>` → `SetAudioCfg`
  - `reolink audio speak-volume --value <n>` → `SetAudioCfg`
  - `reolink audio alarm enable|disable` → `SetAudioAlarm`

- [ ] **4.7** Image controls
  - `reolink image set --brightness <n> ...` → `SetImage`, `SetIsp`

- [ ] **4.8** Encoding controls
  - `reolink encoding set --bitrate <n> --framerate <n>` → `SetEnc`

- [ ] **4.9** OSD controls
  - `reolink osd set --name-pos <p> --watermark on|off` → `SetOsd`

- [ ] **4.10** Privacy mask
  - `reolink privacy-mask enable|disable` → `SetMask`

- [ ] **4.11** Notification toggles
  - `reolink push enable|disable` → `SetPush`
  - `reolink email enable|disable` → `SetEmail`
  - `reolink email test` → `TestEmail`
  - `reolink ftp enable|disable` → `SetFtp`
  - `reolink ftp test` → `TestFtp`
  - `reolink recording enable|disable` → `SetRec`

- [ ] **4.12** System time
  - `reolink time set <iso-datetime>` → `SetTime`
  - `reolink ntp set --server <host>` → `SetNtp`
  - `reolink ntp sync` → sync NTP

- [ ] **4.13** WiFi config
  - `reolink wifi scan` → `ScanWifi`
  - `reolink wifi set <ssid> <password>` → `SetWifi`

- [ ] **4.14** Camera reboot
  - `reolink reboot` → `Reboot` (requires `--force`)

- [ ] **4.15** Firmware
  - `reolink firmware check` → `CheckFirmware`
  - `reolink firmware update` → `UpgradeOnline` (requires `--force`)

### Phase 4 Acceptance
All setter commands work and confirm changes. Destructive commands (reboot, firmware update) require `--force`. State changes verified by re-reading state.

---

## Phase 5: PTZ
*Pan-tilt-zoom commands — separate phase since Argus 4 Pro is fixed, but other Reolink cams have PTZ*

- [ ] **5.1** PTZ movement
  - `reolink ptz move <direction>` → `PtzCtrl`
  - Directions: up, down, left, right, stop
  - `--speed <1-64>`

- [ ] **5.2** PTZ zoom
  - `reolink ptz zoom in|out` → `PtzCtrl` zoom ops

- [ ] **5.3** PTZ focus
  - `reolink ptz focus --value <n>` → `SetZoomFocus`
  - `reolink ptz autofocus enable|disable` → `SetAutoFocus`

- [ ] **5.4** PTZ presets
  - `reolink ptz preset list` → `GetPtzPreset`
  - `reolink ptz preset goto <id>` → `PtzCtrl` (goto preset)
  - `reolink ptz preset set <name>` → `SetPtzPreset`

- [ ] **5.5** PTZ patrol & guard
  - `reolink ptz patrol start|stop` → `PtzCtrl`
  - `reolink ptz guard status|enable|disable` → `GetPtzGuard` / `SetPtzGuard`

- [ ] **5.6** PTZ tracking & position
  - `reolink ptz track enable|disable` → auto tracking
  - `reolink ptz position` → `GetPtzCurPos`
  - `reolink ptz calibrate` → `PtzCheck`

### Phase 5 Acceptance
PTZ commands work on PTZ-capable cameras. Graceful "not supported" (exit 5) on fixed cameras like the Argus 4 Pro.

---

## Phase 6: Webhooks, Users & Advanced
*Less common but important for full coverage*

- [ ] **6.1** Webhook management
  - `reolink webhook add <url>` → webhook registration
  - `reolink webhook test <url>` → test delivery
  - `reolink webhook remove <url>` → unregister
  - `reolink webhook disable <url>` → disable without removing

- [ ] **6.2** User management
  - `reolink users add <name> <pass> --level admin|guest` → `AddUser`
  - `reolink users delete <name>` → `DelUser` (requires `--force`)

- [ ] **6.3** Quick reply (doorbell feature)
  - `reolink quick-reply list` → `GetAudioFileList`
  - `reolink quick-reply play <id>` → `AudioAlarmPlay`

- [ ] **6.4** Raw API escape hatch
  - `reolink raw <command> --body <json>` → send any API command
  - For undocumented or future endpoints without waiting for CLI update

### Phase 6 Acceptance
Full feature parity with the HTTP API. `reolink raw` as the ultimate escape hatch.

---

## Phase 7: Polish & Release
*Make it a proper open-source project*

- [ ] **7.1** Comprehensive README with install instructions, usage examples, supported cameras
- [ ] **7.2** Add shell completion (bash/zsh)
- [ ] **7.3** Add `--config <file>` flag for multi-camera setups (named profiles)
- [ ] **7.4** Add camera discovery (`reolink discover` — ONVIF/SSDP scan)
- [ ] **7.5** Test against Maddy's Argus 4 Pro specifically
- [ ] **7.6** PyPI publish prep (if desired)
- [ ] **7.7** GitHub releases + tags

### Phase 7 Acceptance
`pip install reolink-cli` works. README is clear enough for anyone to get started. Tested against real hardware.

---

## Follow-up (out of scope for this plan)
- OpenClaw skill wrapper (SKILL.md in `~/clawd/skills/`)
- ClawHub publish
- TOOLS.md update

---

## Execution Order & Dependencies

```
Phase 1 (Foundation)     → MUST be first, everything depends on it
Phase 2 (Read commands)  → Depends on Phase 1
Phase 3 (Media)          → Depends on Phase 1
Phase 2 + 3 can run in parallel

Phase 4 (Setters)        → Depends on Phase 2 (need read to verify)
Phase 5 (PTZ)            → Depends on Phase 1
Phase 6 (Advanced)       → Depends on Phase 1

Phase 7 (Polish)         → After all functional phases
```

---

## Estimated Effort

| Phase | Effort | Priority |
|-------|--------|----------|
| 1 — Foundation | ~45 min | 🔴 Critical |
| 2 — Read commands | ~30 min | 🔴 Critical |
| 3 — Media + Watch | ~40 min | 🔴 Critical |
| 4 — Setters | ~45 min | 🟡 High |
| 5 — PTZ | ~20 min | 🟢 Low (Argus 4 Pro is fixed) |
| 6 — Advanced | ~20 min | 🟢 Low |
| 7 — Polish | ~30 min | 🟡 High |

**Total: ~3.5-4 hours for complete implementation**
**MVP (Phases 1-3): ~1.5 hours** — enough to snap, stream, check battery, list recordings

---

## Open Questions

1. ~~Multi-camera support now or later?~~ → **Single camera MVP.** Profiles later.
2. ~~Colour output?~~ → **No colour.** Plain text.
3. ~~`reolink watch`?~~ → **Yes, polling approach.** Added to Phase 3 (task 3.6). Poll every 3-5s, zero new deps, edge-detection for dedup.

---

*Plan lives at: `~/clawd/plans/reolink-cli.md`*
*Track progress by checking off tasks as completed.*
