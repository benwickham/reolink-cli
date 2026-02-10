# CLAUDE.md

This file provides guidance to Claude Code when working on this repository.

## Project Overview

reolink-cli is a command-line interface for controlling Reolink cameras. It wraps the Reolink HTTP API into a human-friendly CLI that is also scriptable for automation and AI agent integration.

**This is an open-source public project.** Write code as if strangers will read it, use it, and contribute to it.

## Tech Stack

- **Language:** Python 3.10+ (must work on 3.10 through 3.14)
- **CLI framework:** argparse (stdlib only — no click/typer)
- **HTTP client:** requests (sole external dependency)
- **Packaging:** pyproject.toml + setuptools
- **Testing:** pytest
- **Entry point:** `reolink` command via `[project.scripts]` in pyproject.toml

## Project Structure

```
reolink_cli/
├── __init__.py          # Package version
├── __main__.py          # python -m reolink_cli
├── cli.py               # Argparse setup, subcommand routing, main()
├── client.py            # ReolinkClient — HTTP transport, auth, token management
├── output.py            # Human + JSON output formatters
└── commands/            # One module per command group
    ├── __init__.py
    ├── device.py        # info, battery, storage, network, time, capabilities
    ├── media.py         # snap, stream, recordings, watch
    ├── detection.py     # motion, ai, pir, alerts
    ├── controls.py      # lights, siren, audio, image, encoding, osd, privacy
    ├── network.py       # wifi, ntp, ports, push, email, ftp, recording toggles
    ├── ptz.py           # PTZ commands (move, zoom, presets, patrol, guard, track)
    └── advanced.py      # webhooks, users, raw API, firmware, reboot
tests/
├── __init__.py
├── conftest.py          # Shared fixtures (mock client, mock responses)
├── test_client.py       # API client tests
└── test_commands.py     # Command output tests
docs/
└── PLAN.md              # Full build plan with task checklist
```

## Common Commands

```bash
# Install in development mode
pip install -e .

# Run CLI
reolink --help
reolink info --host 192.168.1.100 --pass mypassword

# Run tests
pytest
pytest tests/test_client.py -v

# Quick check everything works
pip install -e . && reolink --version && pytest
```

## Architecture

### API Client (`client.py`)

The `ReolinkClient` class handles all communication with the camera:
- POST requests to `http://<host>/cgi-bin/api.cgi?cmd=<Command>&token=<token>`
- Token-based auth: call `Login` first, cache token, include in subsequent requests
- Auto-login on first API call if not already authenticated
- Proper cleanup: `Logout` on exit / context manager
- All API methods return parsed JSON dicts
- Raise typed exceptions for errors (auth, network, API errors, unsupported features)

### Command Modules (`commands/`)

Each module registers subcommands with argparse:
- Export a `register(subparsers)` function that adds commands to the parser
- Each command function receives the parsed args and a `ReolinkClient` instance
- Commands call client methods, format output, print to stdout
- Use the output formatter for consistent human/JSON output

### Output (`output.py`)

- Human mode: plain text, no colour, key-value pairs or simple tables
- JSON mode (`--json`): structured dicts, one JSON object to stdout
- Quiet mode (`--quiet`): suppress informational messages, data only
- Errors always go to stderr

### Config Precedence

`CLI flags > environment variables > defaults`

Environment variables:
- `REOLINK_HOST` — camera IP/hostname
- `REOLINK_USER` — username (default: `admin`)
- `REOLINK_PASS` — password
- `REOLINK_CHANNEL` — channel index (default: `0`)

## Code Style

- **Type hints:** All function signatures must have type hints. Use `from __future__ import annotations` for modern syntax.
- **Docstrings:** Google-style for all public functions and classes.
- **Naming:** `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- **Imports:** stdlib first, then third-party, then local. Absolute imports only.
- **Line length:** 100 characters max.
- **No colour output.** Plain text only. Respect terminal simplicity.
- **f-strings** over `.format()` or `%`.
- **Keep it simple.** This is a CLI wrapper, not a framework. Avoid abstraction for abstraction's sake.

## Error Handling

- **Exit codes:** 0=success, 1=generic failure, 2=invalid usage, 3=auth failure, 4=camera unreachable, 5=feature not supported
- **Network errors:** Catch `requests.ConnectionError`, `requests.Timeout` → exit 4 with clear message
- **Auth errors:** Detect from API response → exit 3
- **Unsupported features:** Camera returns capability error → exit 5 with "not supported on this model"
- **Never print tracebacks** to the user. Catch exceptions, print a human-readable message to stderr, exit with correct code.

## Testing

- Use pytest with fixtures for mock API responses
- Mock the HTTP layer (don't hit real cameras in CI)
- Test both human and JSON output modes
- Test error handling paths (auth failure, network timeout, bad args)
- Keep tests fast — no network calls, no sleeps

## Important Patterns

### Adding a New Command

1. Choose the right module in `commands/` (or create one if new category)
2. Add a function that takes `(args, client)` and returns/prints output
3. Register it in the module's `register(subparsers)` function
4. Add to `cli.py` imports if new module
5. Write tests

### API Call Pattern

```python
def get_device_info(self) -> dict:
    """Get device information."""
    return self._execute("GetDevInfo")
```

Where `_execute` handles token, POST, response parsing, and error handling.

### Destructive Operations

Commands that change camera state (reboot, firmware update, user delete) must:
- Require `--force` flag when run non-interactively
- Print what will happen before doing it
- Confirm success after

## Reference

- **Reolink HTTP API V8 guide:** Community docs at reolink.com/topic/4196
- **reolink_aio library:** github.com/starkillerOG/reolink_aio (reference for endpoint params/responses)
- **Build plan:** See `@docs/PLAN.md` for full task breakdown and phase details
