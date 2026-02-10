"""ReolinkClient — HTTP transport, auth, and token management."""

from __future__ import annotations

import sys
from typing import Any

import requests


# Exit codes
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_AUTH = 3
EXIT_UNREACHABLE = 4
EXIT_UNSUPPORTED = 5


class ReolinkError(Exception):
    """Base exception for Reolink API errors."""

    def __init__(self, message: str, exit_code: int = EXIT_ERROR) -> None:
        super().__init__(message)
        self.exit_code = exit_code


class AuthError(ReolinkError):
    """Authentication failed."""

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message, EXIT_AUTH)


class NetworkError(ReolinkError):
    """Camera unreachable or network error."""

    def __init__(self, message: str = "Camera unreachable") -> None:
        super().__init__(message, EXIT_UNREACHABLE)


class ApiError(ReolinkError):
    """API returned an error response."""


class UnsupportedError(ReolinkError):
    """Feature not supported on this camera model."""

    def __init__(self, message: str = "Feature not supported on this camera model") -> None:
        super().__init__(message, EXIT_UNSUPPORTED)


# Reolink API error codes that indicate auth failure
_AUTH_ERROR_CODES = {-6, -7, 287}

# Reolink API error codes that indicate unsupported feature
_UNSUPPORTED_ERROR_CODES = {-9, -12}


class ReolinkClient:
    """HTTP client for the Reolink camera API.

    Handles token-based authentication, auto-login, and response parsing.
    Use as a context manager for automatic logout on exit.

    Args:
        host: Camera IP or hostname.
        username: Login username (default: "admin").
        password: Login password.
        channel: Camera channel index (default: 0).
        timeout: Request timeout in seconds (default: 10).
    """

    def __init__(
        self,
        host: str,
        password: str,
        username: str = "admin",
        channel: int = 0,
        timeout: int = 10,
    ) -> None:
        self.host = host
        self.username = username
        self.password = password
        self.channel = channel
        self.timeout = timeout
        self._token: str | None = None
        self._base_url = f"http://{host}/cgi-bin/api.cgi"

    def __enter__(self) -> ReolinkClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.logout()

    def _post(self, params: dict[str, str], body: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Send a POST request to the camera API.

        Args:
            params: URL query parameters (cmd, token).
            body: JSON request body (list of command dicts).

        Returns:
            Parsed JSON response (list of result dicts).

        Raises:
            NetworkError: Camera unreachable or request timed out.
        """
        try:
            resp = requests.post(
                self._base_url,
                params=params,
                json=body,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.ConnectionError:
            raise NetworkError(
                f"Cannot connect to camera at {self.host}"
                " — check the IP and ensure you're on the same network"
            )
        except requests.Timeout:
            raise NetworkError(
                f"Connection to {self.host} timed out after {self.timeout}s"
                " — camera may be asleep or unreachable"
            )
        except requests.HTTPError as exc:
            raise NetworkError(f"HTTP error from {self.host}: {exc}")
        except requests.JSONDecodeError:
            raise ApiError(f"Invalid JSON response from {self.host}")

    def login(self) -> None:
        """Authenticate with the camera and store the session token.

        Raises:
            AuthError: If credentials are rejected.
            NetworkError: If camera is unreachable.
        """
        body = [
            {
                "cmd": "Login",
                "action": 0,
                "param": {
                    "User": {
                        "userName": self.username,
                        "password": self.password,
                    }
                },
            }
        ]
        result = self._post({"cmd": "Login"}, body)
        item = result[0] if result else {}

        if "error" in item:
            rsp_code = item["error"].get("rspCode", 0)
            detail = item["error"].get("detail", "unknown error")
            if rsp_code in _AUTH_ERROR_CODES:
                raise AuthError(f"Login failed: {detail}")
            raise ApiError(f"Login error: {detail}")

        token_obj = item.get("value", {}).get("Token", {})
        token = token_obj.get("name")
        if not token:
            raise AuthError("Login succeeded but no token returned")
        self._token = token

    def logout(self) -> None:
        """End the session and release the token.

        Silently ignores errors since this is cleanup.
        """
        if self._token is None:
            return
        try:
            body = [{"cmd": "Logout", "action": 0}]
            self._post({"cmd": "Logout", "token": self._token}, body)
        except ReolinkError:
            pass
        finally:
            self._token = None

    def _ensure_logged_in(self) -> None:
        """Auto-login if no token is present."""
        if self._token is None:
            self.login()

    def execute(self, cmd: str, action: int = 0, param: dict[str, Any] | None = None) -> dict:
        """Execute an API command and return the parsed value.

        Automatically logs in if needed. Handles error responses.

        Args:
            cmd: API command name (e.g. "GetDevInfo").
            action: Action code (0 for GET-style, 1 for SET-style).
            param: Command parameters dict.

        Returns:
            The "value" dict from the API response.

        Raises:
            AuthError: If authentication fails.
            ApiError: If the API returns an error.
            UnsupportedError: If the feature is not supported.
            NetworkError: If the camera is unreachable.
        """
        self._ensure_logged_in()

        body: dict[str, Any] = {"cmd": cmd, "action": action}
        if param is not None:
            body["param"] = param

        result = self._post(
            {"cmd": cmd, "token": self._token},
            [body],
        )
        item = result[0] if result else {}

        if "error" in item:
            rsp_code = item["error"].get("rspCode", 0)
            detail = item["error"].get("detail", "unknown error")
            if rsp_code in _AUTH_ERROR_CODES:
                raise AuthError(f"API auth error: {detail}")
            if rsp_code in _UNSUPPORTED_ERROR_CODES:
                raise UnsupportedError(detail)
            raise ApiError(f"API error ({cmd}): {detail}", EXIT_ERROR)

        # Some commands return code != 0 inside the value
        code = item.get("code", 0)
        if code != 0:
            if code in _AUTH_ERROR_CODES:
                raise AuthError(f"API auth error (code {code})")
            if code in _UNSUPPORTED_ERROR_CODES:
                raise UnsupportedError()
            raise ApiError(f"API error ({cmd}): code {code}", EXIT_ERROR)

        return item.get("value", {})

    def get_device_info(self) -> dict:
        """Get device information.

        Returns:
            Dict with device info (model, firmware, name, etc.).
        """
        value = self.execute("GetDevInfo")
        return value.get("DevInfo", value)

    def get_battery_info(self) -> dict:
        """Get battery status.

        Returns:
            Dict with battery percentage, charging state, temperature, etc.
        """
        value = self.execute("GetBatteryInfo")
        return value.get("BatteryInfo", value)

    def get_hdd_info(self) -> list[dict]:
        """Get storage/HDD information.

        Returns:
            List of dicts, one per storage device (SD card, HDD).
        """
        value = self.execute("GetHddInfo")
        return value.get("HddInfo", [])

    def get_local_link(self) -> dict:
        """Get local network link information.

        Returns:
            Dict with IP, MAC, link type, DNS settings.
        """
        value = self.execute("GetLocalLink")
        return value.get("LocalLink", value)

    def get_net_port(self) -> dict:
        """Get network port configuration.

        Returns:
            Dict with HTTP, HTTPS, RTSP, RTMP, ONVIF port numbers.
        """
        value = self.execute("GetNetPort")
        return value.get("NetPort", value)

    def get_wifi_signal(self) -> int | None:
        """Get WiFi signal strength.

        Returns:
            Signal strength value (dBm), or None if unavailable.
        """
        value = self.execute("GetWifiSignal")
        return value.get("wifiSignal")

    def get_time(self) -> dict:
        """Get system time and timezone settings.

        Returns:
            Dict with Time and Dst (daylight saving) sub-dicts.
        """
        return self.execute("GetTime")

    def get_ability(self) -> dict:
        """Get camera capabilities.

        Returns:
            Dict describing all supported features and their parameters.
        """
        value = self.execute("GetAbility", param={"User": {"userName": self.username}})
        return value.get("Ability", value)

    def get_md_alarm(self) -> dict:
        """Get motion detection alarm configuration.

        Returns:
            Dict with enable state, sensitivity, and schedule.
        """
        value = self.execute("GetMdAlarm", param={"channel": self.channel})
        return value.get("MdAlarm", value)

    def get_md_state(self) -> dict:
        """Get current motion detection state.

        Returns:
            Dict with current motion trigger state.
        """
        return self.execute("GetMdState", param={"channel": self.channel})

    def get_ai_state(self) -> dict:
        """Get current AI detection state.

        Returns:
            Dict with per-type detection states (person, vehicle, animal, etc.).
        """
        return self.execute("GetAiState", param={"channel": self.channel})

    def get_ai_cfg(self) -> dict:
        """Get AI detection configuration.

        Returns:
            Dict with enabled detection types and their settings.
        """
        value = self.execute("GetAiCfg", param={"channel": self.channel})
        return value.get("AiDetectType", value)

    def get_ir_lights(self) -> dict:
        """Get infrared lights status.

        Returns:
            Dict with IR light state and mode.
        """
        value = self.execute("GetIrLights", param={"channel": self.channel})
        return value.get("IrLights", value)

    def get_white_led(self) -> dict:
        """Get white LED (spotlight) status.

        Returns:
            Dict with spotlight state, mode, and brightness.
        """
        value = self.execute("GetWhiteLed", param={"channel": self.channel})
        return value.get("WhiteLed", value)

    def get_power_led(self) -> dict:
        """Get power/status LED state.

        Returns:
            Dict with LED on/off state.
        """
        value = self.execute("GetPowerLed", param={"channel": self.channel})
        return value.get("PowerLed", value)

    def get_image(self) -> dict:
        """Get image settings (brightness, contrast, etc.).

        Returns:
            Dict with image adjustment parameters.
        """
        value = self.execute("GetImage", param={"channel": self.channel})
        return value.get("Image", value)

    def get_isp(self) -> dict:
        """Get ISP settings (day/night mode, exposure, etc.).

        Returns:
            Dict with ISP configuration parameters.
        """
        value = self.execute("GetIsp", param={"channel": self.channel})
        return value.get("Isp", value)

    def get_enc(self) -> dict:
        """Get encoding configuration.

        Returns:
            Dict with main/sub stream encoding settings.
        """
        value = self.execute("GetEnc", param={"channel": self.channel})
        return value.get("Enc", value)

    def get_audio_cfg(self) -> dict:
        """Get audio configuration.

        Returns:
            Dict with mic volume, speaker volume, recording enable state.
        """
        value = self.execute("GetAudioCfg", param={"channel": self.channel})
        return value.get("AudioCfg", value)

    def get_audio_alarm(self) -> dict:
        """Get audio alarm configuration.

        Returns:
            Dict with audio alarm enable state and settings.
        """
        value = self.execute("GetAudioAlarm", param={"channel": self.channel})
        return value.get("AudioAlarm", value)

    def snap(self, stream: str = "main") -> bytes:
        """Capture a JPEG snapshot from the camera.

        Args:
            stream: Stream to capture from ("main" or "sub").

        Returns:
            Raw JPEG bytes.

        Raises:
            NetworkError: If camera is unreachable.
            ApiError: If snapshot capture fails.
        """
        self._ensure_logged_in()
        params = {
            "cmd": "Snap",
            "channel": str(self.channel),
            "token": self._token,
        }
        if stream == "sub":
            params["rs"] = f"{self.channel}0100"
        try:
            resp = requests.get(
                self._base_url,
                params=params,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            if "image" not in resp.headers.get("content-type", ""):
                raise ApiError("Snapshot response is not an image")
            return resp.content
        except requests.ConnectionError:
            raise NetworkError(
                f"Cannot connect to camera at {self.host}"
                " — check the IP and ensure you're on the same network"
            )
        except requests.Timeout:
            raise NetworkError(
                f"Connection to {self.host} timed out after {self.timeout}s"
                " — camera may be asleep or unreachable"
            )
        except requests.HTTPError as exc:
            raise NetworkError(f"HTTP error from {self.host}: {exc}")

    def get_rec(self) -> dict:
        """Get recording configuration.

        Returns:
            Dict with recording schedule, overwrite, pre/post record settings.
        """
        value = self.execute("GetRec", param={"channel": self.channel})
        return value.get("Rec", value)

    def search_recordings(
        self,
        start_time: dict[str, int],
        end_time: dict[str, int],
        only_status: int = 0,
    ) -> list[dict]:
        """Search for recordings in a time range.

        Args:
            start_time: Dict with year, mon, day, hour, min, sec.
            end_time: Dict with year, mon, day, hour, min, sec.
            only_status: 0 = return file list, 1 = return only status.

        Returns:
            List of recording file dicts.
        """
        param = {
            "Search": {
                "channel": self.channel,
                "onlyStatus": only_status,
                "streamType": "main",
                "StartTime": start_time,
                "EndTime": end_time,
            }
        }
        value = self.execute("Search", param=param)
        if "SearchResult" in value:
            result = value["SearchResult"]
            return result.get("File", [])
        return value.get("File", [])

    def download_file(self, filename: str) -> requests.Response:
        """Download a recording file with streaming response.

        Args:
            filename: Recording filename from search results.

        Returns:
            Streaming requests.Response (caller must close).

        Raises:
            NetworkError: If camera is unreachable.
        """
        self._ensure_logged_in()
        params = {
            "cmd": "Download",
            "source": filename,
            "output": filename,
            "token": self._token,
        }
        try:
            resp = requests.get(
                self._base_url,
                params=params,
                timeout=self.timeout,
                stream=True,
            )
            resp.raise_for_status()
            return resp
        except requests.ConnectionError:
            raise NetworkError(
                f"Cannot connect to camera at {self.host}"
                " — check the IP and ensure you're on the same network"
            )
        except requests.Timeout:
            raise NetworkError(
                f"Connection to {self.host} timed out after {self.timeout}s"
                " — camera may be asleep or unreachable"
            )
        except requests.HTTPError as exc:
            raise NetworkError(f"HTTP error from {self.host}: {exc}")

    # -- Phase 4: Setter methods -------------------------------------------------

    def set_md_alarm(self, enable: bool | None = None,
                     sensitivity: int | None = None) -> dict:
        """Set motion detection alarm configuration.

        Args:
            enable: Enable or disable motion detection.
            sensitivity: Sensitivity value (0-100).

        Returns:
            API response value.
        """
        current = self.get_md_alarm()
        md = dict(current)
        md["channel"] = self.channel
        if enable is not None:
            md["enable"] = 1 if enable else 0
        if sensitivity is not None:
            md["sens"] = [{"id": 0, "val": sensitivity}]
        return self.execute("SetMdAlarm", action=1, param={"MdAlarm": md})

    def set_ai_cfg(self, **types: int) -> dict:
        """Set AI detection type configuration.

        Args:
            **types: Detection types to set (e.g. people=1, vehicle=0).

        Returns:
            API response value.
        """
        current = self.get_ai_cfg()
        cfg = dict(current)
        cfg.update(types)
        return self.execute(
            "SetAiCfg", action=1,
            param={"AiDetectType": cfg, "channel": self.channel},
        )

    def set_ir_lights(self, state: str) -> dict:
        """Set infrared lights state.

        Args:
            state: "Auto", "On", or "Off".

        Returns:
            API response value.
        """
        return self.execute(
            "SetIrLights", action=1,
            param={"IrLights": {"channel": self.channel, "state": state}},
        )

    def set_white_led(self, state: int | None = None, mode: int | None = None,
                      brightness: int | None = None) -> dict:
        """Set white LED (spotlight) configuration.

        Args:
            state: 1 for on, 0 for off.
            mode: 0=off, 1=night mode, 3=schedule.
            brightness: Brightness percentage (0-100).

        Returns:
            API response value.
        """
        current = self.get_white_led()
        led = dict(current)
        led["channel"] = self.channel
        if state is not None:
            led["state"] = state
        if mode is not None:
            led["mode"] = mode
        if brightness is not None:
            led["bright"] = brightness
        return self.execute("SetWhiteLed", action=1, param={"WhiteLed": led})

    def set_power_led(self, state: int) -> dict:
        """Set power/status LED state.

        Args:
            state: 1 for on, 0 for off.

        Returns:
            API response value.
        """
        return self.execute(
            "SetPowerLed", action=1,
            param={"PowerLed": {"channel": self.channel, "state": state}},
        )

    def set_image(self, **settings: int) -> dict:
        """Set image settings.

        Args:
            **settings: Image parameters (bright, contrast, saturation, sharpe, hue).

        Returns:
            API response value.
        """
        current = self.get_image()
        img = dict(current)
        img["channel"] = self.channel
        img.update(settings)
        return self.execute("SetImage", action=1, param={"Image": img})

    def set_isp(self, **settings: Any) -> dict:
        """Set ISP settings (flip, mirror, HDR, etc.).

        Args:
            **settings: ISP parameters (rotation, mirroring, hdr, dayNight, etc.).

        Returns:
            API response value.
        """
        current = self.get_isp()
        isp = dict(current)
        isp["channel"] = self.channel
        isp.update(settings)
        return self.execute("SetIsp", action=1, param={"Isp": isp})

    def set_enc(self, stream: str = "main", **settings: Any) -> dict:
        """Set encoding configuration for a stream.

        Args:
            stream: "main" or "sub".
            **settings: Encoding parameters (bitRate, frameRate, size).

        Returns:
            API response value.
        """
        current = self.get_enc()
        enc = dict(current)
        enc["channel"] = self.channel
        key = "mainStream" if stream == "main" else "subStream"
        if key in enc:
            enc[key] = dict(enc[key])
            enc[key].update(settings)
        return self.execute("SetEnc", action=1, param={"Enc": enc})

    def set_audio_cfg(self, **settings: Any) -> dict:
        """Set audio configuration.

        Args:
            **settings: Audio parameters (micVolume, speakerVolume, recordEnable).

        Returns:
            API response value.
        """
        current = self.get_audio_cfg()
        cfg = dict(current)
        cfg["channel"] = self.channel
        cfg.update(settings)
        return self.execute("SetAudioCfg", action=1, param={"AudioCfg": cfg})

    # -- Phase 5: Alert & notification methods -----------------------------------

    def set_audio_alarm(self, enable: bool) -> dict:
        """Set audio alarm enable state.

        Args:
            enable: True to enable, False to disable.

        Returns:
            API response value.
        """
        return self.execute(
            "SetAudioAlarm", action=1,
            param={"AudioAlarm": {"channel": self.channel, "enable": 1 if enable else 0}},
        )

    def audio_alarm_play(self, alarm_mode: str = "manul", manual_switch: int = 0,
                         duration: int = 0) -> dict:
        """Trigger or stop the siren / audio alarm.

        Args:
            alarm_mode: "manul" for manual control, "times" for timed.
                Note: "manul" is the Reolink API's own spelling, not a typo.
            manual_switch: 1 to start, 0 to stop.
            duration: Duration in seconds (for timed mode).

        Returns:
            API response value.
        """
        param: dict[str, Any] = {
            "AudioAlarmPlay": {
                "channel": self.channel,
                "alarm_mode": alarm_mode,
                "manual_switch": manual_switch,
            }
        }
        if duration:
            param["AudioAlarmPlay"]["times"] = duration
        return self.execute("AudioAlarmPlay", action=1, param=param)

    def get_push(self) -> dict:
        """Get push notification configuration.

        Returns:
            Dict with push notification settings.
        """
        value = self.execute("GetPush", param={"channel": self.channel})
        return value.get("Push", value)

    def set_push(self, enable: bool) -> dict:
        """Set push notification enable state.

        Args:
            enable: True to enable, False to disable.

        Returns:
            API response value.
        """
        return self.execute(
            "SetPush", action=1,
            param={"Push": {"channel": self.channel, "enable": 1 if enable else 0}},
        )

    def get_ftp(self) -> dict:
        """Get FTP upload configuration.

        Returns:
            Dict with FTP settings.
        """
        value = self.execute("GetFtp", param={"channel": self.channel})
        return value.get("Ftp", value)

    def set_ftp(self, enable: bool) -> dict:
        """Set FTP upload enable state.

        Args:
            enable: True to enable, False to disable.

        Returns:
            API response value.
        """
        current = self.get_ftp()
        ftp = dict(current)
        ftp["channel"] = self.channel
        ftp["enable"] = 1 if enable else 0
        return self.execute("SetFtp", action=1, param={"Ftp": ftp})

    def test_ftp(self) -> dict:
        """Test FTP connection.

        Returns:
            API response value.
        """
        return self.execute("TestFtp", param={"channel": self.channel})

    def get_email(self) -> dict:
        """Get email alert configuration.

        Returns:
            Dict with email settings.
        """
        value = self.execute("GetEmail", param={"channel": self.channel})
        return value.get("Email", value)

    def set_email(self, enable: bool) -> dict:
        """Set email alert enable state.

        Args:
            enable: True to enable, False to disable.

        Returns:
            API response value.
        """
        current = self.get_email()
        email = dict(current)
        email["channel"] = self.channel
        email["enable"] = 1 if enable else 0
        return self.execute("SetEmail", action=1, param={"Email": email})

    def test_email(self) -> dict:
        """Test email delivery.

        Returns:
            API response value.
        """
        return self.execute("TestEmail", param={"channel": self.channel})

    def set_rec(self, enable: bool) -> dict:
        """Set recording enable state.

        Args:
            enable: True to enable, False to disable.

        Returns:
            API response value.
        """
        current = self.get_rec()
        rec = dict(current)
        rec["channel"] = self.channel
        rec["enable"] = 1 if enable else 0
        return self.execute("SetRec", action=1, param={"Rec": rec})

    # -- Phase 6: System admin methods -------------------------------------------

    def reboot(self) -> dict:
        """Reboot the camera.

        Returns:
            API response value.
        """
        return self.execute("Reboot")

    def get_firmware_info(self) -> dict:
        """Get current firmware information.

        Returns:
            Dict with firmware version info. Same as device info.
        """
        return self.get_device_info()

    def check_firmware(self) -> dict:
        """Check for firmware updates.

        Returns:
            Dict with firmware update availability and version info.
        """
        return self.execute("CheckFirmware")

    def upgrade_online(self) -> dict:
        """Start online firmware upgrade.

        Returns:
            API response value.
        """
        return self.execute("UpgradeOnline")

    def set_time(self, time_settings: dict[str, Any]) -> dict:
        """Set system time.

        Args:
            time_settings: Dict with Time and optionally Dst sub-dicts.

        Returns:
            API response value.
        """
        return self.execute("SetTime", action=1, param=time_settings)

    def get_ntp(self) -> dict:
        """Get NTP configuration.

        Returns:
            Dict with NTP server settings.
        """
        value = self.execute("GetNtp")
        return value.get("Ntp", value)

    def set_ntp(self, **settings: Any) -> dict:
        """Set NTP configuration.

        Args:
            **settings: NTP parameters (enable, server, port, interval).

        Returns:
            API response value.
        """
        current = self.get_ntp()
        ntp = dict(current)
        ntp.update(settings)
        return self.execute("SetNtp", action=1, param={"Ntp": ntp})

    def get_user(self) -> list[dict]:
        """Get user list.

        Returns:
            List of user dicts.
        """
        value = self.execute("GetUser")
        return value.get("User", [])

    def get_online(self) -> list[dict]:
        """Get currently online sessions.

        Returns:
            List of online session dicts.
        """
        value = self.execute("GetOnline")
        return value.get("Online", [])

    def add_user(self, username: str, password: str, level: str = "guest") -> dict:
        """Add a new user.

        Args:
            username: New username.
            password: New password.
            level: Permission level ("admin" or "guest").

        Returns:
            API response value.
        """
        return self.execute(
            "AddUser", action=1,
            param={"User": {"userName": username, "password": password, "level": level}},
        )

    def delete_user(self, username: str) -> dict:
        """Delete a user.

        Args:
            username: Username to delete.

        Returns:
            API response value.
        """
        return self.execute(
            "DelUser", action=1,
            param={"User": {"userName": username}},
        )
