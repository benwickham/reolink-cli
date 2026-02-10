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
    API_ERROR_RESPONSE,
    DEVICE_INFO_RESPONSE,
    LOGIN_FAILURE_RESPONSE,
    LOGIN_SUCCESS_RESPONSE,
    UNSUPPORTED_RESPONSE,
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
