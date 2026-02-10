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
            raise NetworkError(f"Cannot connect to camera at {self.host}")
        except requests.Timeout:
            raise NetworkError(f"Connection to {self.host} timed out after {self.timeout}s")
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
