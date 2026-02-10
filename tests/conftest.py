"""Shared fixtures for reolink-cli tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from reolink_cli.client import ReolinkClient


# ---------------------------------------------------------------------------
# Sample API responses
# ---------------------------------------------------------------------------

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

BATTERY_INFO_RESPONSE = [
    {
        "cmd": "GetBatteryInfo",
        "code": 0,
        "value": {
            "BatteryInfo": {
                "batteryPercent": 85,
                "chargeStatus": 1,
                "temperature": 25,
                "lowPower": 0,
                "sleepState": 0,
                "adapterStatus": 1,
            }
        },
    }
]

HDD_INFO_RESPONSE = [
    {
        "cmd": "GetHddInfo",
        "code": 0,
        "value": {
            "HddInfo": [
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
        },
    }
]

LOCAL_LINK_RESPONSE = [
    {
        "cmd": "GetLocalLink",
        "code": 0,
        "value": {
            "LocalLink": {
                "activeLink": "WiFi",
                "mac": "AA:BB:CC:DD:EE:FF",
                "type": "DHCP",
                "static": {
                    "ip": "192.168.1.100",
                    "mask": "255.255.255.0",
                    "gateway": "192.168.1.1",
                },
                "dns": {
                    "auto": 1,
                    "dns1": "8.8.8.8",
                    "dns2": "8.8.4.4",
                },
            }
        },
    }
]

NET_PORT_RESPONSE = [
    {
        "cmd": "GetNetPort",
        "code": 0,
        "value": {
            "NetPort": {
                "httpPort": 80,
                "httpsPort": 443,
                "rtspPort": 554,
                "rtmpPort": 1935,
                "onvifPort": 8000,
                "mediaPort": 9000,
            }
        },
    }
]

WIFI_SIGNAL_RESPONSE = [
    {
        "cmd": "GetWifiSignal",
        "code": 0,
        "value": {"wifiSignal": -45},
    }
]

TIME_RESPONSE = [
    {
        "cmd": "GetTime",
        "code": 0,
        "value": {
            "Dst": {"enable": 0},
            "Time": {
                "day": 10,
                "hour": 14,
                "hourFmt": 0,
                "min": 30,
                "mon": 2,
                "sec": 0,
                "timeFmt": "DD/MM/YYYY",
                "timeZone": -28800,
                "year": 2026,
            },
        },
    }
]

ABILITY_RESPONSE = [
    {
        "cmd": "GetAbility",
        "code": 0,
        "value": {
            "Ability": {
                "abilityChn": [
                    {
                        "aiTrack": {"ver": 0},
                        "batAnalysis": {"ver": 1},
                        "live": {"ver": 1},
                        "ptz": {"ver": 0},
                        "snap": {"ver": 1},
                    }
                ],
                "channelNum": 1,
            }
        },
    }
]

MD_ALARM_RESPONSE = [
    {
        "cmd": "GetMdAlarm",
        "code": 0,
        "value": {
            "MdAlarm": {
                "channel": 0,
                "enable": 1,
                "sens": [{"id": 0, "val": 50}],
            }
        },
    }
]

MD_STATE_RESPONSE = [
    {
        "cmd": "GetMdState",
        "code": 0,
        "value": {"channel": 0, "state": 0},
    }
]

AI_STATE_RESPONSE = [
    {
        "cmd": "GetAiState",
        "code": 0,
        "value": {
            "channel": 0,
            "dog_cat": {"alarm_state": 0, "support": 1},
            "face": {"alarm_state": 0, "support": 0},
            "people": {"alarm_state": 1, "support": 1},
            "vehicle": {"alarm_state": 0, "support": 1},
        },
    }
]

AI_CFG_RESPONSE = [
    {
        "cmd": "GetAiCfg",
        "code": 0,
        "value": {
            "AiDetectType": {
                "dog_cat": 1,
                "face": 0,
                "people": 1,
                "vehicle": 1,
            }
        },
    }
]

IR_LIGHTS_RESPONSE = [
    {
        "cmd": "GetIrLights",
        "code": 0,
        "value": {
            "IrLights": {"channel": 0, "state": "Auto"}
        },
    }
]

WHITE_LED_RESPONSE = [
    {
        "cmd": "GetWhiteLed",
        "code": 0,
        "value": {
            "WhiteLed": {
                "channel": 0,
                "state": 1,
                "mode": 1,
                "bright": 75,
            }
        },
    }
]

POWER_LED_RESPONSE = [
    {
        "cmd": "GetPowerLed",
        "code": 0,
        "value": {
            "PowerLed": {"channel": 0, "state": 1}
        },
    }
]

IMAGE_RESPONSE = [
    {
        "cmd": "GetImage",
        "code": 0,
        "value": {
            "Image": {
                "channel": 0,
                "bright": 128,
                "contrast": 128,
                "saturation": 128,
                "sharpe": 128,
                "hue": 128,
            }
        },
    }
]

ISP_RESPONSE = [
    {
        "cmd": "GetIsp",
        "code": 0,
        "value": {
            "Isp": {
                "channel": 0,
                "antiFlicker": "Outdoor",
                "dayNight": "Auto",
                "exposure": "Auto",
                "whiteBalance": "Auto",
                "hdr": 1,
                "rotation": 0,
                "mirroring": 0,
            }
        },
    }
]

ENC_RESPONSE = [
    {
        "cmd": "GetEnc",
        "code": 0,
        "value": {
            "Enc": {
                "channel": 0,
                "mainStream": {
                    "bitRate": 4096,
                    "frameRate": 15,
                    "profile": "Main",
                    "size": "3840*2160",
                    "video": {"codec": "h265"},
                },
                "subStream": {
                    "bitRate": 512,
                    "frameRate": 15,
                    "profile": "Main",
                    "size": "640*360",
                    "video": {"codec": "h264"},
                },
            }
        },
    }
]

AUDIO_CFG_RESPONSE = [
    {
        "cmd": "GetAudioCfg",
        "code": 0,
        "value": {
            "AudioCfg": {
                "channel": 0,
                "micVolume": 80,
                "speakerVolume": 90,
                "recordEnable": 1,
            }
        },
    }
]

AUDIO_ALARM_RESPONSE = [
    {
        "cmd": "GetAudioAlarm",
        "code": 0,
        "value": {
            "AudioAlarm": {"channel": 0, "enable": 1}
        },
    }
]

REC_RESPONSE = [
    {
        "cmd": "GetRec",
        "code": 0,
        "value": {
            "Rec": {
                "channel": 0,
                "enable": 1,
                "overwrite": 1,
                "packDuration": 600,
                "preRec": 1,
                "postRec": 10,
                "schedule": {"enable": 1},
            }
        },
    }
]

SEARCH_RESPONSE = [
    {
        "cmd": "Search",
        "code": 0,
        "value": {
            "SearchResult": {
                "Status": {"mon": 2, "table": "111"},
                "File": [
                    {
                        "name": "/mnt/sd/20260210/rec/001.mp4",
                        "StartTime": {
                            "year": 2026, "mon": 2, "day": 10,
                            "hour": 8, "min": 30, "sec": 0,
                        },
                        "EndTime": {
                            "year": 2026, "mon": 2, "day": 10,
                            "hour": 8, "min": 35, "sec": 0,
                        },
                        "size": 10485760,
                        "type": "alarm",
                    },
                    {
                        "name": "/mnt/sd/20260210/rec/002.mp4",
                        "StartTime": {
                            "year": 2026, "mon": 2, "day": 10,
                            "hour": 10, "min": 0, "sec": 0,
                        },
                        "EndTime": {
                            "year": 2026, "mon": 2, "day": 10,
                            "hour": 10, "min": 10, "sec": 0,
                        },
                        "size": 20971520,
                        "type": "schedule",
                    },
                ],
            }
        },
    }
]

SET_SUCCESS_RESPONSE = [
    {
        "cmd": "SetMdAlarm",
        "code": 0,
        "value": {"rspCode": 200},
    }
]

PUSH_RESPONSE = [
    {
        "cmd": "GetPush",
        "code": 0,
        "value": {
            "Push": {"channel": 0, "enable": 1}
        },
    }
]

FTP_RESPONSE = [
    {
        "cmd": "GetFtp",
        "code": 0,
        "value": {
            "Ftp": {"channel": 0, "enable": 0, "server": "ftp.example.com"}
        },
    }
]

EMAIL_RESPONSE = [
    {
        "cmd": "GetEmail",
        "code": 0,
        "value": {
            "Email": {"channel": 0, "enable": 0, "addr1": "test@example.com"}
        },
    }
]

NTP_RESPONSE = [
    {
        "cmd": "GetNtp",
        "code": 0,
        "value": {
            "Ntp": {"enable": 1, "server": "pool.ntp.org", "port": 123, "interval": 1440}
        },
    }
]

USER_RESPONSE = [
    {
        "cmd": "GetUser",
        "code": 0,
        "value": {
            "User": [
                {"userName": "admin", "level": "admin"},
                {"userName": "viewer", "level": "guest"},
            ]
        },
    }
]

ONLINE_RESPONSE = [
    {
        "cmd": "GetOnline",
        "code": 0,
        "value": {
            "Online": [
                {"userName": "admin", "ip": "192.168.1.50"},
            ]
        },
    }
]

CHECK_FIRMWARE_RESPONSE = [
    {
        "cmd": "CheckFirmware",
        "code": 0,
        "value": {
            "firmVer": "v3.1.0.2347",
            "newFirmVer": "v3.2.0.100",
            "needUpgrade": 1,
        },
    }
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

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
