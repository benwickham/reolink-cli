"""Tests for output formatters."""

from __future__ import annotations

import json

from reolink_cli.output import format_human, format_json, output


class TestFormatHuman:
    """Tests for human-readable formatting."""

    def test_simple_dict(self):
        result = format_human({"Name": "Front Door", "Model": "Argus 4 Pro"})
        assert "Name" in result
        assert "Front Door" in result
        assert "Model" in result
        assert "Argus 4 Pro" in result

    def test_with_title(self):
        result = format_human({"a": 1}, title="Test")
        assert result.startswith("Test\n")
        assert "----" in result

    def test_empty_dict(self):
        result = format_human({})
        assert result == ""

    def test_empty_dict_with_title(self):
        result = format_human({}, title="Empty")
        assert "Empty" in result

    def test_alignment(self):
        result = format_human({"Short": "a", "LongerKey": "b"})
        lines = [l for l in result.split("\n") if l.strip()]
        # Both values should start at the same column
        pos_a = lines[0].index("a")
        pos_b = lines[1].index("b")
        assert pos_a == pos_b


class TestFormatJson:
    """Tests for JSON formatting."""

    def test_dict(self):
        data = {"model": "Argus 4 Pro", "channels": 1}
        result = format_json(data)
        parsed = json.loads(result)
        assert parsed == data

    def test_nested(self):
        data = {"info": {"name": "cam"}}
        result = format_json(data)
        parsed = json.loads(result)
        assert parsed["info"]["name"] == "cam"


class TestOutput:
    """Tests for the output() function."""

    def test_json_mode(self, capsys):
        output({"key": "val"}, json_mode=True)
        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert parsed["key"] == "val"

    def test_human_mode(self, capsys):
        output({"Name": "test"}, title="Info")
        captured = capsys.readouterr()
        assert "Info" in captured.out
        assert "Name" in captured.out
        assert "test" in captured.out

    def test_quiet_mode(self, capsys):
        output({"key": "val"}, quiet=True)
        captured = capsys.readouterr()
        assert captured.out == ""
