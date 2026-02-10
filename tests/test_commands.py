"""Tests for CLI commands — output formatting and argument handling."""

from __future__ import annotations

import json
from argparse import Namespace
from unittest.mock import MagicMock, patch

import pytest

from reolink_cli.cli import main
from reolink_cli.client import AuthError, NetworkError, UnsupportedError


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

SAMPLE_BATTERY_INFO = {
    "batteryPercent": 85,
    "chargeStatus": 1,
    "temperature": 25,
    "lowPower": 0,
    "sleepState": 0,
    "adapterStatus": 1,
}

SAMPLE_HDD_INFO = [
    {
        "id": 0,
        "capacity": 29.44,
        "mount": 1,
        "size": 29.44,
        "used": 15.2,
        "free": 14.24,
        "storageType": "SD",
        "overWrite": 1,
        "health": "normal",
    }
]

SAMPLE_LOCAL_LINK = {
    "activeLink": "WiFi",
    "mac": "AA:BB:CC:DD:EE:FF",
    "type": "DHCP",
    "static": {"ip": "192.168.1.100", "mask": "255.255.255.0", "gateway": "192.168.1.1"},
    "dns": {"auto": 1, "dns1": "8.8.8.8", "dns2": "8.8.4.4"},
}

SAMPLE_NET_PORT = {
    "httpPort": 80,
    "httpsPort": 443,
    "rtspPort": 554,
    "rtmpPort": 1935,
    "onvifPort": 8000,
    "mediaPort": 9000,
}

SAMPLE_TIME = {
    "Dst": {"enable": 0},
    "Time": {
        "day": 10, "hour": 14, "hourFmt": 0, "min": 30, "mon": 2,
        "sec": 0, "timeFmt": "DD/MM/YYYY", "timeZone": -28800, "year": 2026,
    },
}

SAMPLE_ABILITY = {
    "abilityChn": [{"aiTrack": {"ver": 0}, "ptz": {"ver": 0}, "snap": {"ver": 1}}],
    "channelNum": 1,
}

SAMPLE_MD_ALARM = {"channel": 0, "enable": 1, "sens": [{"id": 0, "val": 50}]}
SAMPLE_MD_STATE = {"channel": 0, "state": 0}

SAMPLE_AI_STATE = {
    "channel": 0,
    "dog_cat": {"alarm_state": 0, "support": 1},
    "face": {"alarm_state": 0, "support": 0},
    "people": {"alarm_state": 1, "support": 1},
    "vehicle": {"alarm_state": 0, "support": 1},
}

SAMPLE_AI_CFG = {"dog_cat": 1, "face": 0, "people": 1, "vehicle": 1}

SAMPLE_IR_LIGHTS = {"channel": 0, "state": "Auto"}

SAMPLE_WHITE_LED = {"channel": 0, "state": 1, "mode": 1, "bright": 75}

SAMPLE_POWER_LED = {"channel": 0, "state": 1}

SAMPLE_IMAGE = {"channel": 0, "bright": 128, "contrast": 128, "saturation": 128, "sharpe": 128, "hue": 128}

SAMPLE_ISP = {
    "channel": 0, "antiFlicker": "Outdoor", "dayNight": "Auto",
    "exposure": "Auto", "whiteBalance": "Auto", "hdr": 1, "rotation": 0, "mirroring": 0,
}

SAMPLE_ENC = {
    "channel": 0,
    "mainStream": {
        "bitRate": 4096, "frameRate": 15, "profile": "Main",
        "size": "3840*2160", "video": {"codec": "h265"},
    },
    "subStream": {
        "bitRate": 512, "frameRate": 15, "profile": "Main",
        "size": "640*360", "video": {"codec": "h264"},
    },
}

SAMPLE_AUDIO_CFG = {"channel": 0, "micVolume": 80, "speakerVolume": 90, "recordEnable": 1}
SAMPLE_AUDIO_ALARM = {"channel": 0, "enable": 1}


# ---------------------------------------------------------------------------
# Info command
# ---------------------------------------------------------------------------

class TestInfoCommand:
    """Tests for the 'info' command."""

    @patch("reolink_cli.commands.device.output")
    def test_info_human(self, mock_output):
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
        from reolink_cli.commands.device import _cmd_info

        args = Namespace(json=True)
        client = MagicMock()
        client.get_device_info.return_value = SAMPLE_DEVICE_INFO

        _cmd_info(args, client)

        mock_output.assert_called_once_with(SAMPLE_DEVICE_INFO, json_mode=True)


# ---------------------------------------------------------------------------
# Battery command
# ---------------------------------------------------------------------------

class TestBatteryCommand:
    """Tests for the 'battery' command."""

    @patch("reolink_cli.commands.device.output")
    def test_battery_human(self, mock_output):
        from reolink_cli.commands.device import _cmd_battery

        args = Namespace(json=False)
        client = MagicMock()
        client.get_battery_info.return_value = SAMPLE_BATTERY_INFO

        _cmd_battery(args, client)

        mock_output.assert_called_once()
        data = mock_output.call_args[0][0]
        assert data["Battery"] == "85%"
        assert data["Charging"] == "Charging"
        assert data["Temperature"] == "25°C"
        assert mock_output.call_args[1]["title"] == "Battery Status"

    @patch("reolink_cli.commands.device.output")
    def test_battery_json(self, mock_output):
        from reolink_cli.commands.device import _cmd_battery

        args = Namespace(json=True)
        client = MagicMock()
        client.get_battery_info.return_value = SAMPLE_BATTERY_INFO

        _cmd_battery(args, client)

        mock_output.assert_called_once_with(SAMPLE_BATTERY_INFO, json_mode=True)


# ---------------------------------------------------------------------------
# Storage command
# ---------------------------------------------------------------------------

class TestStorageCommand:
    """Tests for the 'storage' command."""

    @patch("reolink_cli.commands.device.output")
    def test_storage_human(self, mock_output):
        from reolink_cli.commands.device import _cmd_storage

        args = Namespace(json=False)
        client = MagicMock()
        client.get_hdd_info.return_value = SAMPLE_HDD_INFO

        _cmd_storage(args, client)

        mock_output.assert_called_once()
        data = mock_output.call_args[0][0]
        assert data["Capacity"] == "29.44 GB"
        assert data["Type"] == "SD"
        assert data["Overwrite"] == "Enabled"
        assert data["Health"] == "normal"

    @patch("reolink_cli.commands.device.output")
    def test_storage_json(self, mock_output):
        from reolink_cli.commands.device import _cmd_storage

        args = Namespace(json=True)
        client = MagicMock()
        client.get_hdd_info.return_value = SAMPLE_HDD_INFO

        _cmd_storage(args, client)

        mock_output.assert_called_once_with(SAMPLE_HDD_INFO, json_mode=True)

    @patch("reolink_cli.commands.device.output")
    def test_storage_empty(self, mock_output):
        from reolink_cli.commands.device import _cmd_storage

        args = Namespace(json=False)
        client = MagicMock()
        client.get_hdd_info.return_value = []

        _cmd_storage(args, client)

        mock_output.assert_called_once()
        data = mock_output.call_args[0][0]
        assert "Status" in data


# ---------------------------------------------------------------------------
# Network command
# ---------------------------------------------------------------------------

class TestNetworkCommand:
    """Tests for the 'network' command."""

    @patch("reolink_cli.commands.device.output")
    def test_network_human(self, mock_output):
        from reolink_cli.commands.device import _cmd_network

        args = Namespace(json=False)
        client = MagicMock()
        client.get_local_link.return_value = SAMPLE_LOCAL_LINK
        client.get_net_port.return_value = SAMPLE_NET_PORT
        client.get_wifi_signal.return_value = -45

        _cmd_network(args, client)

        mock_output.assert_called_once()
        data = mock_output.call_args[0][0]
        assert data["Connection"] == "WiFi"
        assert data["MAC"] == "AA:BB:CC:DD:EE:FF"
        assert data["IP"] == "192.168.1.100"
        assert data["RTSP Port"] == "554"
        assert data["WiFi Signal"] == "-45 dBm"

    @patch("reolink_cli.commands.device.output")
    def test_network_json(self, mock_output):
        from reolink_cli.commands.device import _cmd_network

        args = Namespace(json=True)
        client = MagicMock()
        client.get_local_link.return_value = SAMPLE_LOCAL_LINK
        client.get_net_port.return_value = SAMPLE_NET_PORT
        client.get_wifi_signal.return_value = -45

        _cmd_network(args, client)

        mock_output.assert_called_once()
        data = mock_output.call_args[0][0]
        assert data["localLink"] == SAMPLE_LOCAL_LINK
        assert data["ports"] == SAMPLE_NET_PORT
        assert data["wifiSignal"] == -45

    @patch("reolink_cli.commands.device.output")
    def test_network_no_wifi(self, mock_output):
        from reolink_cli.commands.device import _cmd_network

        args = Namespace(json=False)
        client = MagicMock()
        client.get_local_link.return_value = SAMPLE_LOCAL_LINK
        client.get_net_port.return_value = SAMPLE_NET_PORT
        client.get_wifi_signal.side_effect = UnsupportedError()

        _cmd_network(args, client)

        data = mock_output.call_args[0][0]
        assert "WiFi Signal" not in data


# ---------------------------------------------------------------------------
# Time command
# ---------------------------------------------------------------------------

class TestTimeCommand:
    """Tests for the 'time' command."""

    @patch("reolink_cli.commands.device.output")
    def test_time_human(self, mock_output):
        from reolink_cli.commands.device import _cmd_time

        args = Namespace(json=False)
        client = MagicMock()
        client.get_time.return_value = SAMPLE_TIME

        _cmd_time(args, client)

        mock_output.assert_called_once()
        data = mock_output.call_args[0][0]
        assert data["Time"] == "2026-02-10 14:30:00"
        assert data["Timezone"] == "UTC-8"
        assert data["Hour Format"] == "24h"
        assert data["DST"] == "Disabled"

    @patch("reolink_cli.commands.device.output")
    def test_time_json(self, mock_output):
        from reolink_cli.commands.device import _cmd_time

        args = Namespace(json=True)
        client = MagicMock()
        client.get_time.return_value = SAMPLE_TIME

        _cmd_time(args, client)

        mock_output.assert_called_once_with(SAMPLE_TIME, json_mode=True)


# ---------------------------------------------------------------------------
# Capabilities command
# ---------------------------------------------------------------------------

class TestCapabilitiesCommand:
    """Tests for the 'capabilities' command."""

    def test_capabilities_json_output(self, capsys):
        from reolink_cli.commands.device import _cmd_capabilities

        args = Namespace(json=False)
        client = MagicMock()
        client.get_ability.return_value = SAMPLE_ABILITY

        _cmd_capabilities(args, client)

        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert parsed["channelNum"] == 1


# ---------------------------------------------------------------------------
# Motion status command
# ---------------------------------------------------------------------------

class TestMotionStatusCommand:
    """Tests for the 'motion status' command."""

    @patch("reolink_cli.commands.detection.output")
    def test_motion_status_human(self, mock_output):
        from reolink_cli.commands.detection import _cmd_motion_status

        args = Namespace(json=False)
        client = MagicMock()
        client.get_md_alarm.return_value = SAMPLE_MD_ALARM
        client.get_md_state.return_value = SAMPLE_MD_STATE

        _cmd_motion_status(args, client)

        mock_output.assert_called_once()
        data = mock_output.call_args[0][0]
        assert data["Enabled"] == "Yes"
        assert data["Motion"] == "Idle"
        assert "Sensitivity" in data

    @patch("reolink_cli.commands.detection.output")
    def test_motion_status_json(self, mock_output):
        from reolink_cli.commands.detection import _cmd_motion_status

        args = Namespace(json=True)
        client = MagicMock()
        client.get_md_alarm.return_value = SAMPLE_MD_ALARM
        client.get_md_state.return_value = SAMPLE_MD_STATE

        _cmd_motion_status(args, client)

        mock_output.assert_called_once()
        data = mock_output.call_args[0][0]
        assert data["alarm"] == SAMPLE_MD_ALARM
        assert data["state"] == SAMPLE_MD_STATE


# ---------------------------------------------------------------------------
# AI status command
# ---------------------------------------------------------------------------

class TestAiStatusCommand:
    """Tests for the 'ai status' command."""

    @patch("reolink_cli.commands.detection.output")
    def test_ai_status_human(self, mock_output):
        from reolink_cli.commands.detection import _cmd_ai_status

        args = Namespace(json=False)
        client = MagicMock()
        client.get_ai_state.return_value = SAMPLE_AI_STATE
        client.get_ai_cfg.return_value = SAMPLE_AI_CFG

        _cmd_ai_status(args, client)

        mock_output.assert_called_once()
        data = mock_output.call_args[0][0]
        assert "Person" in data
        assert "Vehicle" in data
        assert "Animal" in data
        # Face has support=0, should be excluded
        assert "Face" not in data

    @patch("reolink_cli.commands.detection.output")
    def test_ai_status_json(self, mock_output):
        from reolink_cli.commands.detection import _cmd_ai_status

        args = Namespace(json=True)
        client = MagicMock()
        client.get_ai_state.return_value = SAMPLE_AI_STATE
        client.get_ai_cfg.return_value = SAMPLE_AI_CFG

        _cmd_ai_status(args, client)

        mock_output.assert_called_once()
        data = mock_output.call_args[0][0]
        assert data["state"] == SAMPLE_AI_STATE
        assert data["config"] == SAMPLE_AI_CFG

    @patch("reolink_cli.commands.detection.output")
    def test_ai_status_no_cfg(self, mock_output):
        """AI config not supported should still work."""
        from reolink_cli.commands.detection import _cmd_ai_status

        args = Namespace(json=False)
        client = MagicMock()
        client.get_ai_state.return_value = SAMPLE_AI_STATE
        client.get_ai_cfg.side_effect = UnsupportedError()

        _cmd_ai_status(args, client)

        data = mock_output.call_args[0][0]
        assert "Person" in data


# ---------------------------------------------------------------------------
# IR status command
# ---------------------------------------------------------------------------

class TestIrStatusCommand:
    """Tests for the 'ir status' command."""

    @patch("reolink_cli.commands.controls.output")
    def test_ir_status_human(self, mock_output):
        from reolink_cli.commands.controls import _cmd_ir_status

        args = Namespace(json=False)
        client = MagicMock()
        client.get_ir_lights.return_value = SAMPLE_IR_LIGHTS

        _cmd_ir_status(args, client)

        data = mock_output.call_args[0][0]
        assert data["State"] == "Auto"

    @patch("reolink_cli.commands.controls.output")
    def test_ir_status_json(self, mock_output):
        from reolink_cli.commands.controls import _cmd_ir_status

        args = Namespace(json=True)
        client = MagicMock()
        client.get_ir_lights.return_value = SAMPLE_IR_LIGHTS

        _cmd_ir_status(args, client)

        mock_output.assert_called_once_with(SAMPLE_IR_LIGHTS, json_mode=True)


# ---------------------------------------------------------------------------
# Spotlight status command
# ---------------------------------------------------------------------------

class TestSpotlightStatusCommand:
    """Tests for the 'spotlight status' command."""

    @patch("reolink_cli.commands.controls.output")
    def test_spotlight_status_human(self, mock_output):
        from reolink_cli.commands.controls import _cmd_spotlight_status

        args = Namespace(json=False)
        client = MagicMock()
        client.get_white_led.return_value = SAMPLE_WHITE_LED

        _cmd_spotlight_status(args, client)

        data = mock_output.call_args[0][0]
        assert data["State"] == "On"
        assert data["Mode"] == "Night Mode"
        assert data["Brightness"] == "75%"

    @patch("reolink_cli.commands.controls.output")
    def test_spotlight_status_json(self, mock_output):
        from reolink_cli.commands.controls import _cmd_spotlight_status

        args = Namespace(json=True)
        client = MagicMock()
        client.get_white_led.return_value = SAMPLE_WHITE_LED

        _cmd_spotlight_status(args, client)

        mock_output.assert_called_once_with(SAMPLE_WHITE_LED, json_mode=True)


# ---------------------------------------------------------------------------
# Status LED command
# ---------------------------------------------------------------------------

class TestStatusLedCommand:
    """Tests for the 'status-led' command."""

    @patch("reolink_cli.commands.controls.output")
    def test_status_led_human(self, mock_output):
        from reolink_cli.commands.controls import _cmd_status_led

        args = Namespace(json=False)
        client = MagicMock()
        client.get_power_led.return_value = SAMPLE_POWER_LED

        _cmd_status_led(args, client)

        data = mock_output.call_args[0][0]
        assert data["State"] == "On"

    @patch("reolink_cli.commands.controls.output")
    def test_status_led_json(self, mock_output):
        from reolink_cli.commands.controls import _cmd_status_led

        args = Namespace(json=True)
        client = MagicMock()
        client.get_power_led.return_value = SAMPLE_POWER_LED

        _cmd_status_led(args, client)

        mock_output.assert_called_once_with(SAMPLE_POWER_LED, json_mode=True)


# ---------------------------------------------------------------------------
# Image status command
# ---------------------------------------------------------------------------

class TestImageStatusCommand:
    """Tests for the 'image status' command."""

    @patch("reolink_cli.commands.controls.output")
    def test_image_status_human(self, mock_output):
        from reolink_cli.commands.controls import _cmd_image_status

        args = Namespace(json=False)
        client = MagicMock()
        client.get_image.return_value = SAMPLE_IMAGE
        client.get_isp.return_value = SAMPLE_ISP

        _cmd_image_status(args, client)

        data = mock_output.call_args[0][0]
        assert data["Brightness"] == "128"
        assert data["Day/Night"] == "Auto"
        assert data["HDR"] == "On"

    @patch("reolink_cli.commands.controls.output")
    def test_image_status_json(self, mock_output):
        from reolink_cli.commands.controls import _cmd_image_status

        args = Namespace(json=True)
        client = MagicMock()
        client.get_image.return_value = SAMPLE_IMAGE
        client.get_isp.return_value = SAMPLE_ISP

        _cmd_image_status(args, client)

        data = mock_output.call_args[0][0]
        assert data["image"] == SAMPLE_IMAGE
        assert data["isp"] == SAMPLE_ISP


# ---------------------------------------------------------------------------
# Encoding status command
# ---------------------------------------------------------------------------

class TestEncodingStatusCommand:
    """Tests for the 'encoding status' command."""

    @patch("reolink_cli.commands.controls.output")
    def test_encoding_status_human(self, mock_output):
        from reolink_cli.commands.controls import _cmd_encoding_status

        args = Namespace(json=False)
        client = MagicMock()
        client.get_enc.return_value = SAMPLE_ENC

        _cmd_encoding_status(args, client)

        data = mock_output.call_args[0][0]
        assert data["Main Resolution"] == "3840*2160"
        assert data["Main Bitrate"] == "4096 kbps"
        assert data["Main Codec"] == "h265"
        assert data["Sub Resolution"] == "640*360"
        assert data["Sub Codec"] == "h264"

    @patch("reolink_cli.commands.controls.output")
    def test_encoding_status_json(self, mock_output):
        from reolink_cli.commands.controls import _cmd_encoding_status

        args = Namespace(json=True)
        client = MagicMock()
        client.get_enc.return_value = SAMPLE_ENC

        _cmd_encoding_status(args, client)

        mock_output.assert_called_once_with(SAMPLE_ENC, json_mode=True)


# ---------------------------------------------------------------------------
# Audio status command
# ---------------------------------------------------------------------------

class TestAudioStatusCommand:
    """Tests for the 'audio status' command."""

    @patch("reolink_cli.commands.controls.output")
    def test_audio_status_human(self, mock_output):
        from reolink_cli.commands.controls import _cmd_audio_status

        args = Namespace(json=False)
        client = MagicMock()
        client.get_audio_cfg.return_value = SAMPLE_AUDIO_CFG
        client.get_audio_alarm.return_value = SAMPLE_AUDIO_ALARM

        _cmd_audio_status(args, client)

        data = mock_output.call_args[0][0]
        assert data["Mic Volume"] == "80"
        assert data["Speaker Volume"] == "90"
        assert data["Recording"] == "On"
        assert data["Audio Alarm"] == "Enabled"

    @patch("reolink_cli.commands.controls.output")
    def test_audio_status_json(self, mock_output):
        from reolink_cli.commands.controls import _cmd_audio_status

        args = Namespace(json=True)
        client = MagicMock()
        client.get_audio_cfg.return_value = SAMPLE_AUDIO_CFG
        client.get_audio_alarm.return_value = SAMPLE_AUDIO_ALARM

        _cmd_audio_status(args, client)

        data = mock_output.call_args[0][0]
        assert data["config"] == SAMPLE_AUDIO_CFG
        assert data["alarm"] == SAMPLE_AUDIO_ALARM


# ---------------------------------------------------------------------------
# CLI main tests
# ---------------------------------------------------------------------------

class TestCLIMain:
    """Tests for the main CLI entry point."""

    def test_help(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "reolink" in captured.out
        assert "info" in captured.out

    def test_help_shows_all_commands(self, capsys):
        with pytest.raises(SystemExit):
            main(["--help"])
        captured = capsys.readouterr()
        for cmd in ["info", "battery", "storage", "network", "time", "capabilities",
                     "motion", "ai", "ir", "spotlight", "status-led",
                     "image", "encoding", "audio"]:
            assert cmd in captured.out, f"'{cmd}' not in help output"

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
