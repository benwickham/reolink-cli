"""Tests for ReolinkClient — auth, token management, error handling."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from reolink_cli.client import (
    ApiError,
    AuthError,
    NetworkError,
    ReolinkClient,
    UnsupportedError,
)
from tests.conftest import (
    ABILITY_RESPONSE,
    AI_CFG_RESPONSE,
    AI_STATE_RESPONSE,
    API_ERROR_RESPONSE,
    AUDIO_ALARM_RESPONSE,
    AUDIO_CFG_RESPONSE,
    BATTERY_INFO_RESPONSE,
    DEVICE_INFO_RESPONSE,
    ENC_RESPONSE,
    HDD_INFO_RESPONSE,
    IMAGE_RESPONSE,
    IR_LIGHTS_RESPONSE,
    ISP_RESPONSE,
    LOCAL_LINK_RESPONSE,
    LOGIN_FAILURE_RESPONSE,
    LOGIN_SUCCESS_RESPONSE,
    MD_ALARM_RESPONSE,
    MD_STATE_RESPONSE,
    NET_PORT_RESPONSE,
    POWER_LED_RESPONSE,
    TIME_RESPONSE,
    UNSUPPORTED_RESPONSE,
    WHITE_LED_RESPONSE,
    WIFI_SIGNAL_RESPONSE,
)


class TestLogin:
    """Tests for login/logout flow."""

    def test_login_success(self, client, mock_post, mock_response):
        mock_response.json.return_value = LOGIN_SUCCESS_RESPONSE
        mock_post.return_value = mock_response

        client.login()
        assert client._token == "abc123token"
        mock_post.assert_called_once()

    def test_login_auth_failure(self, client, mock_post, mock_response):
        mock_response.json.return_value = LOGIN_FAILURE_RESPONSE
        mock_post.return_value = mock_response

        with pytest.raises(AuthError, match="login failed"):
            client.login()
        assert client._token is None

    def test_login_network_error(self, client, mock_post):
        mock_post.side_effect = requests.ConnectionError("refused")

        with pytest.raises(NetworkError, match="Cannot connect"):
            client.login()

    def test_login_timeout(self, client, mock_post):
        mock_post.side_effect = requests.Timeout("timed out")

        with pytest.raises(NetworkError, match="timed out"):
            client.login()

    def test_logout(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = [{"cmd": "Logout", "code": 0, "value": {}}]
        mock_post.return_value = mock_response

        logged_in_client.logout()
        assert logged_in_client._token is None

    def test_logout_without_login(self, client):
        # Should not raise
        client.logout()

    def test_context_manager(self, mock_post, mock_response):
        mock_response.json.return_value = LOGIN_SUCCESS_RESPONSE
        mock_post.return_value = mock_response

        with ReolinkClient("192.168.1.100", "pass") as c:
            c.login()
            assert c._token == "abc123token"
        # After exit, logout should have been called
        assert c._token is None


class TestExecute:
    """Tests for API command execution."""

    def test_execute_auto_login(self, client, mock_post, mock_response):
        # First call returns login, second returns device info
        mock_response.json.side_effect = [
            LOGIN_SUCCESS_RESPONSE,
            DEVICE_INFO_RESPONSE,
        ]
        mock_post.return_value = mock_response

        result = client.execute("GetDevInfo")
        assert result["DevInfo"]["model"] == "Argus 4 Pro"
        assert mock_post.call_count == 2  # login + execute

    def test_execute_already_logged_in(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = DEVICE_INFO_RESPONSE
        mock_post.return_value = mock_response

        result = logged_in_client.execute("GetDevInfo")
        assert result["DevInfo"]["model"] == "Argus 4 Pro"

    def test_execute_api_error(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = API_ERROR_RESPONSE
        mock_post.return_value = mock_response

        with pytest.raises(ApiError, match="something went wrong"):
            logged_in_client.execute("GetDevInfo")

    def test_execute_unsupported(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = UNSUPPORTED_RESPONSE
        mock_post.return_value = mock_response

        with pytest.raises(UnsupportedError):
            logged_in_client.execute("GetPtzPreset")

    def test_execute_auth_error(self, logged_in_client, mock_post, mock_response):
        auth_err_response = [
            {
                "cmd": "GetDevInfo",
                "code": 0,
                "error": {"detail": "please login first", "rspCode": -6},
            }
        ]
        mock_response.json.return_value = auth_err_response
        mock_post.return_value = mock_response

        with pytest.raises(AuthError):
            logged_in_client.execute("GetDevInfo")


class TestGetDeviceInfo:
    """Tests for the get_device_info convenience method."""

    def test_get_device_info(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = DEVICE_INFO_RESPONSE
        mock_post.return_value = mock_response

        info = logged_in_client.get_device_info()
        assert info["model"] == "Argus 4 Pro"
        assert info["name"] == "Front Door"
        assert info["channelNum"] == 1


class TestGetBatteryInfo:
    """Tests for battery info retrieval."""

    def test_get_battery_info(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = BATTERY_INFO_RESPONSE
        mock_post.return_value = mock_response

        info = logged_in_client.get_battery_info()
        assert info["batteryPercent"] == 85
        assert info["chargeStatus"] == 1
        assert info["temperature"] == 25


class TestGetHddInfo:
    """Tests for storage info retrieval."""

    def test_get_hdd_info(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = HDD_INFO_RESPONSE
        mock_post.return_value = mock_response

        info = logged_in_client.get_hdd_info()
        assert len(info) == 1
        assert info[0]["capacity"] == 29.44
        assert info[0]["storageType"] == "SD"


class TestGetNetworkInfo:
    """Tests for network info retrieval."""

    def test_get_local_link(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = LOCAL_LINK_RESPONSE
        mock_post.return_value = mock_response

        info = logged_in_client.get_local_link()
        assert info["activeLink"] == "WiFi"
        assert info["mac"] == "AA:BB:CC:DD:EE:FF"

    def test_get_net_port(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = NET_PORT_RESPONSE
        mock_post.return_value = mock_response

        info = logged_in_client.get_net_port()
        assert info["rtspPort"] == 554
        assert info["httpPort"] == 80

    def test_get_wifi_signal(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = WIFI_SIGNAL_RESPONSE
        mock_post.return_value = mock_response

        signal = logged_in_client.get_wifi_signal()
        assert signal == -45


class TestGetTime:
    """Tests for time retrieval."""

    def test_get_time(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = TIME_RESPONSE
        mock_post.return_value = mock_response

        info = logged_in_client.get_time()
        assert "Time" in info
        assert info["Time"]["year"] == 2026
        assert info["Time"]["mon"] == 2


class TestGetAbility:
    """Tests for capability retrieval."""

    def test_get_ability(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = ABILITY_RESPONSE
        mock_post.return_value = mock_response

        info = logged_in_client.get_ability()
        assert "channelNum" in info
        assert info["channelNum"] == 1


class TestGetDetection:
    """Tests for motion and AI detection retrieval."""

    def test_get_md_alarm(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = MD_ALARM_RESPONSE
        mock_post.return_value = mock_response

        info = logged_in_client.get_md_alarm()
        assert info["enable"] == 1

    def test_get_md_state(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = MD_STATE_RESPONSE
        mock_post.return_value = mock_response

        info = logged_in_client.get_md_state()
        assert info["state"] == 0

    def test_get_ai_state(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = AI_STATE_RESPONSE
        mock_post.return_value = mock_response

        info = logged_in_client.get_ai_state()
        assert info["people"]["alarm_state"] == 1
        assert info["vehicle"]["support"] == 1

    def test_get_ai_cfg(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = AI_CFG_RESPONSE
        mock_post.return_value = mock_response

        info = logged_in_client.get_ai_cfg()
        assert info["people"] == 1
        assert info["dog_cat"] == 1


class TestGetControls:
    """Tests for light, image, encoding, and audio retrieval."""

    def test_get_ir_lights(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = IR_LIGHTS_RESPONSE
        mock_post.return_value = mock_response

        info = logged_in_client.get_ir_lights()
        assert info["state"] == "Auto"

    def test_get_white_led(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = WHITE_LED_RESPONSE
        mock_post.return_value = mock_response

        info = logged_in_client.get_white_led()
        assert info["state"] == 1
        assert info["bright"] == 75

    def test_get_power_led(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = POWER_LED_RESPONSE
        mock_post.return_value = mock_response

        info = logged_in_client.get_power_led()
        assert info["state"] == 1

    def test_get_image(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = IMAGE_RESPONSE
        mock_post.return_value = mock_response

        info = logged_in_client.get_image()
        assert info["bright"] == 128
        assert info["contrast"] == 128

    def test_get_isp(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = ISP_RESPONSE
        mock_post.return_value = mock_response

        info = logged_in_client.get_isp()
        assert info["dayNight"] == "Auto"
        assert info["hdr"] == 1

    def test_get_enc(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = ENC_RESPONSE
        mock_post.return_value = mock_response

        info = logged_in_client.get_enc()
        assert info["mainStream"]["bitRate"] == 4096
        assert info["subStream"]["video"]["codec"] == "h264"

    def test_get_audio_cfg(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = AUDIO_CFG_RESPONSE
        mock_post.return_value = mock_response

        info = logged_in_client.get_audio_cfg()
        assert info["micVolume"] == 80
        assert info["recordEnable"] == 1

    def test_get_audio_alarm(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = AUDIO_ALARM_RESPONSE
        mock_post.return_value = mock_response

        info = logged_in_client.get_audio_alarm()
        assert info["enable"] == 1


class TestClientInit:
    """Tests for client initialization."""

    def test_defaults(self):
        c = ReolinkClient("192.168.1.1", "pass")
        assert c.host == "192.168.1.1"
        assert c.username == "admin"
        assert c.password == "pass"
        assert c.channel == 0
        assert c.timeout == 10
        assert c._token is None

    def test_custom_params(self):
        c = ReolinkClient("10.0.0.1", "secret", username="user2", channel=1, timeout=30)
        assert c.host == "10.0.0.1"
        assert c.username == "user2"
        assert c.channel == 1
        assert c.timeout == 30
