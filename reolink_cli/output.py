"""Output formatters for human-readable and JSON modes."""

from __future__ import annotations

import json
import sys
from typing import Any


def print_error(message: str) -> None:
    """Print an error message to stderr.

    Args:
        message: Error message to display.
    """
    print(f"Error: {message}", file=sys.stderr)


def format_human(data: dict[str, Any], title: str | None = None) -> str:
    """Format a dict as human-readable key-value pairs.

    Args:
        data: Dict of key-value pairs to display.
        title: Optional title printed above the data.

    Returns:
        Formatted string with aligned key-value pairs.
    """
    lines: list[str] = []
    if title:
        lines.append(title)
        lines.append("-" * len(title))
    if not data:
        return "\n".join(lines) if lines else ""
    max_key = max(len(str(k)) for k in data)
    for key, value in data.items():
        label = str(key).ljust(max_key)
        lines.append(f"  {label}  {value}")
    return "\n".join(lines)


def format_json(data: Any) -> str:
    """Format data as a JSON string.

    Args:
        data: Any JSON-serializable data.

    Returns:
        Pretty-printed JSON string.
    """
    return json.dumps(data, indent=2)


def output(data: dict[str, Any], *, json_mode: bool = False, quiet: bool = False,
           title: str | None = None) -> None:
    """Print data to stdout in the appropriate format.

    Args:
        data: Data to display.
        json_mode: If True, output as JSON.
        quiet: If True, suppress output entirely.
        title: Optional title for human mode.
    """
    if quiet:
        return
    if json_mode:
        print(format_json(data))
    else:
        print(format_human(data, title=title))
