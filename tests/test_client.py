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
    CHECK_FIRMWARE_RESPONSE,
    DEVICE_INFO_RESPONSE,
    EMAIL_RESPONSE,
    ENC_RESPONSE,
    FTP_RESPONSE,
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
    NTP_RESPONSE,
    ONLINE_RESPONSE,
    POWER_LED_RESPONSE,
    PUSH_RESPONSE,
    REC_RESPONSE,
    SEARCH_RESPONSE,
    SET_SUCCESS_RESPONSE,
    TIME_RESPONSE,
    UNSUPPORTED_RESPONSE,
    USER_RESPONSE,
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


class TestSnap:
    """Tests for snapshot capture."""

    @patch("reolink_cli.client.requests.get")
    def test_snap(self, mock_get, logged_in_client):
        mock_resp = MagicMock()
        mock_resp.headers = {"content-type": "image/jpeg"}
        mock_resp.content = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        data = logged_in_client.snap()
        assert data.startswith(b"\xff\xd8")
        mock_get.assert_called_once()

    @patch("reolink_cli.client.requests.get")
    def test_snap_network_error(self, mock_get, logged_in_client):
        mock_get.side_effect = requests.ConnectionError("refused")

        with pytest.raises(NetworkError, match="Cannot connect"):
            logged_in_client.snap()


class TestGetRec:
    """Tests for recording config retrieval."""

    def test_get_rec(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = REC_RESPONSE
        mock_post.return_value = mock_response

        info = logged_in_client.get_rec()
        assert info["enable"] == 1
        assert info["overwrite"] == 1
        assert info["packDuration"] == 600


class TestSearchRecordings:
    """Tests for recording search."""

    def test_search_recordings(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = SEARCH_RESPONSE
        mock_post.return_value = mock_response

        files = logged_in_client.search_recordings(
            start_time={"year": 2026, "mon": 2, "day": 10, "hour": 0, "min": 0, "sec": 0},
            end_time={"year": 2026, "mon": 2, "day": 10, "hour": 23, "min": 59, "sec": 59},
        )
        assert len(files) == 2
        assert files[0]["name"] == "/mnt/sd/20260210/rec/001.mp4"
        assert files[1]["type"] == "schedule"


class TestSetters:
    """Tests for setter methods."""

    def test_set_md_alarm(self, logged_in_client, mock_post, mock_response):
        mock_response.json.side_effect = [MD_ALARM_RESPONSE, SET_SUCCESS_RESPONSE]
        mock_post.return_value = mock_response

        logged_in_client.set_md_alarm(enable=False)
        assert mock_post.call_count >= 2

    def test_set_ir_lights(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = SET_SUCCESS_RESPONSE
        mock_post.return_value = mock_response

        logged_in_client.set_ir_lights("Off")

    def test_set_white_led(self, logged_in_client, mock_post, mock_response):
        mock_response.json.side_effect = [WHITE_LED_RESPONSE, SET_SUCCESS_RESPONSE]
        mock_post.return_value = mock_response

        logged_in_client.set_white_led(state=0)

    def test_set_power_led(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = SET_SUCCESS_RESPONSE
        mock_post.return_value = mock_response

        logged_in_client.set_power_led(0)

    def test_set_image(self, logged_in_client, mock_post, mock_response):
        mock_response.json.side_effect = [IMAGE_RESPONSE, SET_SUCCESS_RESPONSE]
        mock_post.return_value = mock_response

        logged_in_client.set_image(bright=200)

    def test_set_isp(self, logged_in_client, mock_post, mock_response):
        mock_response.json.side_effect = [ISP_RESPONSE, SET_SUCCESS_RESPONSE]
        mock_post.return_value = mock_response

        logged_in_client.set_isp(rotation=180)

    def test_set_enc(self, logged_in_client, mock_post, mock_response):
        mock_response.json.side_effect = [ENC_RESPONSE, SET_SUCCESS_RESPONSE]
        mock_post.return_value = mock_response

        logged_in_client.set_enc(stream="main", bitRate=2048)

    def test_set_audio_cfg(self, logged_in_client, mock_post, mock_response):
        mock_response.json.side_effect = [AUDIO_CFG_RESPONSE, SET_SUCCESS_RESPONSE]
        mock_post.return_value = mock_response

        logged_in_client.set_audio_cfg(micVolume=50)

    def test_set_ai_cfg(self, logged_in_client, mock_post, mock_response):
        mock_response.json.side_effect = [AI_CFG_RESPONSE, SET_SUCCESS_RESPONSE]
        mock_post.return_value = mock_response

        logged_in_client.set_ai_cfg(people=0)


class TestAlertMethods:
    """Tests for alert and notification methods."""

    def test_set_audio_alarm(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = SET_SUCCESS_RESPONSE
        mock_post.return_value = mock_response

        logged_in_client.set_audio_alarm(enable=True)

    def test_audio_alarm_play(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = SET_SUCCESS_RESPONSE
        mock_post.return_value = mock_response

        logged_in_client.audio_alarm_play(manual_switch=1)

    def test_get_push(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = PUSH_RESPONSE
        mock_post.return_value = mock_response

        info = logged_in_client.get_push()
        assert info["enable"] == 1

    def test_set_push(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = SET_SUCCESS_RESPONSE
        mock_post.return_value = mock_response

        logged_in_client.set_push(enable=False)

    def test_get_ftp(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = FTP_RESPONSE
        mock_post.return_value = mock_response

        info = logged_in_client.get_ftp()
        assert info["server"] == "ftp.example.com"

    def test_set_ftp(self, logged_in_client, mock_post, mock_response):
        mock_response.json.side_effect = [FTP_RESPONSE, SET_SUCCESS_RESPONSE]
        mock_post.return_value = mock_response

        logged_in_client.set_ftp(enable=True)

    def test_get_email(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = EMAIL_RESPONSE
        mock_post.return_value = mock_response

        info = logged_in_client.get_email()
        assert info["addr1"] == "test@example.com"

    def test_set_email(self, logged_in_client, mock_post, mock_response):
        mock_response.json.side_effect = [EMAIL_RESPONSE, SET_SUCCESS_RESPONSE]
        mock_post.return_value = mock_response

        logged_in_client.set_email(enable=True)

    def test_set_rec(self, logged_in_client, mock_post, mock_response):
        mock_response.json.side_effect = [REC_RESPONSE, SET_SUCCESS_RESPONSE]
        mock_post.return_value = mock_response

        logged_in_client.set_rec(enable=False)


class TestSystemAdmin:
    """Tests for system admin methods."""

    def test_reboot(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = SET_SUCCESS_RESPONSE
        mock_post.return_value = mock_response

        logged_in_client.reboot()

    def test_check_firmware(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = CHECK_FIRMWARE_RESPONSE
        mock_post.return_value = mock_response

        info = logged_in_client.check_firmware()
        assert info["needUpgrade"] == 1

    def test_get_ntp(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = NTP_RESPONSE
        mock_post.return_value = mock_response

        info = logged_in_client.get_ntp()
        assert info["server"] == "pool.ntp.org"

    def test_set_ntp(self, logged_in_client, mock_post, mock_response):
        mock_response.json.side_effect = [NTP_RESPONSE, SET_SUCCESS_RESPONSE]
        mock_post.return_value = mock_response

        logged_in_client.set_ntp(server="time.google.com")

    def test_get_user(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = USER_RESPONSE
        mock_post.return_value = mock_response

        users = logged_in_client.get_user()
        assert len(users) == 2
        assert users[0]["userName"] == "admin"

    def test_get_online(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = ONLINE_RESPONSE
        mock_post.return_value = mock_response

        sessions = logged_in_client.get_online()
        assert len(sessions) == 1

    def test_add_user(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = SET_SUCCESS_RESPONSE
        mock_post.return_value = mock_response

        logged_in_client.add_user("newuser", "pass123", level="guest")

    def test_delete_user(self, logged_in_client, mock_post, mock_response):
        mock_response.json.return_value = SET_SUCCESS_RESPONSE
        mock_post.return_value = mock_response

        logged_in_client.delete_user("olduser")
