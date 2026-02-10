"""Tests for CLI commands — output formatting and argument handling."""

from __future__ import annotations

import json
from argparse import Namespace
from unittest.mock import MagicMock, patch

import pytest

from reolink_cli.cli import main
from reolink_cli.client import AuthError, NetworkError


SAMPLE_DEVICE_INFO = {
    "name": "Front Door",
    "model": "Argus 4 Pro",
    "firmVer": "v3.1.0.2347",
    "hardVer": "IPC_523B18D8MP_V2",
    "serial": "00000000000000",
    "channelNum": 1,
    "buildDay": "build 24082800",
    "wifi": 1,
}


class TestInfoCommand:
    """Tests for the 'info' command."""

    @patch("reolink_cli.commands.device.output")
    def test_info_human(self, mock_output):
        """Test info command in human mode."""
        from reolink_cli.commands.device import _cmd_info

        args = Namespace(json=False)
        client = MagicMock()
        client.get_device_info.return_value = SAMPLE_DEVICE_INFO

        _cmd_info(args, client)

        mock_output.assert_called_once()
        call_kwargs = mock_output.call_args
        data = call_kwargs[0][0]
        assert "Name" in data
        assert data["Name"] == "Front Door"
        assert data["Model"] == "Argus 4 Pro"
        assert call_kwargs[1]["title"] == "Device Info"

    @patch("reolink_cli.commands.device.output")
    def test_info_json(self, mock_output):
        """Test info command in JSON mode."""
        from reolink_cli.commands.device import _cmd_info

        args = Namespace(json=True)
        client = MagicMock()
        client.get_device_info.return_value = SAMPLE_DEVICE_INFO

        _cmd_info(args, client)

        mock_output.assert_called_once_with(SAMPLE_DEVICE_INFO, json_mode=True)


class TestCLIMain:
    """Tests for the main CLI entry point."""

    def test_help(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "reolink" in captured.out
        assert "info" in captured.out

    def test_version(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "reolink-cli" in captured.out

    def test_no_command(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main([])
        assert exc_info.value.code == 2

    def test_missing_host(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["--password", "pass", "info"])
        assert exc_info.value.code == 2

    def test_missing_password(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["--host", "192.168.1.1", "info"])
        assert exc_info.value.code == 2

    @patch("reolink_cli.cli.ReolinkClient")
    def test_auth_error_exit_code(self, MockClient, capsys):
        instance = MockClient.return_value
        instance.__enter__ = MagicMock(return_value=instance)
        instance.__exit__ = MagicMock(return_value=False)
        instance.get_device_info.side_effect = AuthError("bad creds")

        with pytest.raises(SystemExit) as exc_info:
            main(["--host", "192.168.1.1", "--password", "wrong", "info"])
        assert exc_info.value.code == 3
        assert "bad creds" in capsys.readouterr().err

    @patch("reolink_cli.cli.ReolinkClient")
    def test_network_error_exit_code(self, MockClient, capsys):
        instance = MockClient.return_value
        instance.__enter__ = MagicMock(return_value=instance)
        instance.__exit__ = MagicMock(return_value=False)
        instance.get_device_info.side_effect = NetworkError("unreachable")

        with pytest.raises(SystemExit) as exc_info:
            main(["--host", "192.168.1.1", "--password", "pass", "info"])
        assert exc_info.value.code == 4
        assert "unreachable" in capsys.readouterr().err


class TestCLIEnvVars:
    """Tests for environment variable configuration."""

    @patch.dict("os.environ", {"REOLINK_HOST": "10.0.0.1", "REOLINK_PASS": "envpass"})
    @patch("reolink_cli.cli.ReolinkClient")
    def test_env_vars(self, MockClient):
        instance = MockClient.return_value
        instance.__enter__ = MagicMock(return_value=instance)
        instance.__exit__ = MagicMock(return_value=False)
        instance.get_device_info.return_value = SAMPLE_DEVICE_INFO

        try:
            main(["info"])
        except SystemExit:
            pass

        MockClient.assert_called_once_with(
            host="10.0.0.1",
            password="envpass",
            username="admin",
            channel=0,
            timeout=10,
        )

    @patch.dict("os.environ", {
        "REOLINK_HOST": "10.0.0.1",
        "REOLINK_PASS": "envpass",
        "REOLINK_USER": "envuser",
        "REOLINK_CHANNEL": "2",
    })
    @patch("reolink_cli.cli.ReolinkClient")
    def test_env_vars_all(self, MockClient):
        instance = MockClient.return_value
        instance.__enter__ = MagicMock(return_value=instance)
        instance.__exit__ = MagicMock(return_value=False)
        instance.get_device_info.return_value = SAMPLE_DEVICE_INFO

        try:
            main(["info"])
        except SystemExit:
            pass

        MockClient.assert_called_once_with(
            host="10.0.0.1",
            password="envpass",
            username="envuser",
            channel=2,
            timeout=10,
        )

    @patch.dict("os.environ", {"REOLINK_HOST": "10.0.0.1", "REOLINK_PASS": "envpass"})
    @patch("reolink_cli.cli.ReolinkClient")
    def test_cli_flags_override_env(self, MockClient):
        instance = MockClient.return_value
        instance.__enter__ = MagicMock(return_value=instance)
        instance.__exit__ = MagicMock(return_value=False)
        instance.get_device_info.return_value = SAMPLE_DEVICE_INFO

        try:
            main(["--host", "192.168.1.1", "--password", "clipass", "info"])
        except SystemExit:
            pass

        MockClient.assert_called_once_with(
            host="192.168.1.1",
            password="clipass",
            username="admin",
            channel=0,
            timeout=10,
        )
