"""Shared fixtures for reolink-cli tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from reolink_cli.client import ReolinkClient


# Sample API responses for testing
DEVICE_INFO_RESPONSE = [
    {
        "cmd": "GetDevInfo",
        "code": 0,
        "value": {
            "DevInfo": {
                "B485": 0,
                "IOInputNum": 0,
                "IOOutputNum": 0,
                "buildDay": "build 24082800",
                "cfgVer": "v3.1.0.0",
                "channelNum": 1,
                "detail": "IPC_523B18D8MP_V2",
                "diskNum": 1,
                "exactType": "IPC",
                "firmVer": "v3.1.0.2347_24082800_v1.0.0.93",
                "hardVer": "IPC_523B18D8MP_V2",
                "model": "Argus 4 Pro",
                "name": "Front Door",
                "pakSuffix": "pak",
                "serial": "00000000000000",
                "uid": "",
                "wifi": 1,
            }
        },
    }
]

LOGIN_SUCCESS_RESPONSE = [
    {
        "cmd": "Login",
        "code": 0,
        "value": {
            "Token": {
                "leaseTime": 3600,
                "name": "abc123token",
            }
        },
    }
]

LOGIN_FAILURE_RESPONSE = [
    {
        "cmd": "Login",
        "code": 0,
        "error": {
            "detail": "login failed",
            "rspCode": -6,
        },
    }
]

API_ERROR_RESPONSE = [
    {
        "cmd": "GetDevInfo",
        "code": 0,
        "error": {
            "detail": "something went wrong",
            "rspCode": -1,
        },
    }
]

UNSUPPORTED_RESPONSE = [
    {
        "cmd": "GetPtzPreset",
        "code": 0,
        "error": {
            "detail": "not supported",
            "rspCode": -9,
        },
    }
]


@pytest.fixture
def mock_post():
    """Patch requests.post and return the mock."""
    with patch("reolink_cli.client.requests.post") as mock:
        yield mock


@pytest.fixture
def mock_response():
    """Create a mock response object."""
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    return resp


@pytest.fixture
def client():
    """Create a ReolinkClient instance for testing."""
    return ReolinkClient(
        host="192.168.1.100",
        password="testpass",
        username="admin",
    )


@pytest.fixture
def logged_in_client(client, mock_post, mock_response):
    """Create a ReolinkClient that is already logged in."""
    mock_response.json.return_value = LOGIN_SUCCESS_RESPONSE
    mock_post.return_value = mock_response
    client.login()
    return client
