"""Shared, rate-limited API client and update coordinator."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging
from collections import Counter
from typing import Any
from zoneinfo import ZoneInfo

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DATA_URL, DOMAIN, TOKEN_URL

_LOGGER = logging.getLogger(__name__)
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)


class EGDPowerDataCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Fetch both profiles together once per interval for all entities."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=None)
        self.hass = hass
        self.entry = entry
        self.ean: str = entry.data["ean"]
        self.days: int = int(entry.data.get("days", 1))
        self._session = async_get_clientsession(hass)
        self._token: str | None = None
        self._token_expires_at = datetime.min.replace(tzinfo=UTC)

    @callback
    def _scheduled_refresh(self, now: datetime) -> None:
        """Refresh once daily after EGD normally publishes new readings."""
        self.hass.async_create_task(self.async_request_refresh())

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch consumption and production data in one coordinator cycle."""
        try:
            token = await self._async_get_access_token()
            start, end = self._period()
            params = {
                "ean": self.ean,
                "from": start.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "to": end.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "pageSize": 3000,
            }
            headers = {"Authorization": f"Bearer {token}"}
            results: dict[str, dict[str, Any]] = {}
            for profile in ("ICQ2", "ISQ2", "ICCS"):
                async with self._session.get(
                    DATA_URL,
                    headers=headers,
                    params={**params, "profile": profile},
                    timeout=REQUEST_TIMEOUT,
                ) as response:
                    if response.status >= 400 and profile == "ICCS":
                        value = None
                        details = {
                            "data_status": f"Optional profile unavailable (HTTP {response.status})",
                            "reading_count": 0,
                            "api_reported_total": 0,
                        }
                        payload = None
                    else:
                        response.raise_for_status()
                        payload = await response.json()
                if payload is not None and _LOGGER.isEnabledFor(logging.DEBUG):
                    _LOGGER.debug(
                        "EGD API profile %s response: %s",
                        profile,
                        self._redact_sensitive_data(payload),
                    )
                if payload is not None:
                    try:
                        value, details = self._parse_profile(payload, profile)
                    except ValueError as err:
                        if profile != "ICCS":
                            raise ValueError(f"Profile {profile}: {err}") from err
                        value = None
                        details = {
                            "data_status": "Optional profile unavailable",
                            "profile_error": str(err)[:160],
                            "reading_count": 0,
                            "api_reported_total": 0,
                        }
                results[profile] = {
                    "value": value,
                    "attributes": {
                        **details,
                        "profile": profile,
                        "ean": self.ean,
                        "data_date": start.date().isoformat(),
                        "measurement_period": "previous_day",
                        "local_stime": start.strftime("%Y-%m-%d %H:%M:%S %Z%z"),
                        "local_etime": end.strftime("%Y-%m-%d %H:%M:%S %Z%z"),
                        "stime": params["from"],
                        "etime": params["to"],
                    },
                }
                if _LOGGER.isEnabledFor(logging.DEBUG):
                    _LOGGER.debug(
                        "Parsed EGD profile %s: value=%s, units=%s, readings=%s, statuses=%s",
                        profile,
                        value,
                        details.get("units"),
                        details.get("reading_count"),
                        details.get("status_counts"),
                    )
                if value is None and profile != "ICCS":
                    _LOGGER.warning("EGD returned no readings for profile %s", profile)
            return results
        except (aiohttp.ClientError, TimeoutError, ValueError, KeyError, TypeError) as err:
            raise UpdateFailed(f"EGD API request failed: {err}") from err

    def _period(self) -> tuple[datetime, datetime]:
        """Build the local EGD billing-day range."""
        local_tz = ZoneInfo("Europe/Prague")
        now = datetime.now(local_tz)
        start = (now - timedelta(days=self.days)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end = (now - timedelta(days=1)).replace(
            hour=23, minute=45, second=0, microsecond=0
        )
        return start, end

    @staticmethod
    def _redact_sensitive_data(payload: Any) -> Any:
        """Remove account identifiers and credentials from debug payload logs."""
        sensitive_keys = {
            "ean",
            "eic",
            "ean/eic",
            "access_token",
            "client_secret",
            "authorization",
        }
        if isinstance(payload, dict):
            return {
                key: EGDPowerDataCoordinator._redact_sensitive_data(value)
                for key, value in payload.items()
                if str(key).casefold() not in sensitive_keys
            }
        if isinstance(payload, list):
            return [
                EGDPowerDataCoordinator._redact_sensitive_data(item)
                for item in payload
            ]
        return payload

    async def _async_get_access_token(self) -> str:
        """Return a cached OAuth token or request a new one."""
        now = datetime.now(UTC)
        if self._token and now < self._token_expires_at:
            return self._token

        data = {
            "grant_type": "client_credentials",
            "client_id": self.entry.data[CONF_CLIENT_ID],
            "client_secret": self.entry.data[CONF_CLIENT_SECRET],
            "scope": "namerena_data_openapi",
        }
        async with self._session.post(
            TOKEN_URL, data=data, timeout=REQUEST_TIMEOUT
        ) as response:
            response.raise_for_status()
            payload = await response.json()
        token = payload.get("access_token")
        if not token:
            raise UpdateFailed("EGD OAuth response did not contain an access token")
        self._token = token
        local_now = datetime.now(ZoneInfo("Europe/Prague"))
        self._token_expires_at = local_now.replace(
            hour=23, minute=59, second=0, microsecond=0
        ).astimezone(UTC)
        return token

    @staticmethod
    def _parse_profile(payload: Any, profile: str) -> tuple[float | None, dict[str, Any]]:
        """Convert a profile response to daily kWh and retain useful diagnostics."""
        # EG.D may return a single matching profile as an object instead of an array.
        if isinstance(payload, dict) and payload.get("profile") == profile:
            payload = [payload]
        if not isinstance(payload, list):
            if isinstance(payload, dict):
                message = payload.get("message") or payload.get("error_description") or payload.get("error")
                response_hint = f"object keys={','.join(str(key) for key in list(payload)[:8])}"
                if isinstance(message, str):
                    response_hint += f", message={message[:120]}"
                raise ValueError(f"expected a list of profiles, received {response_hint}")
            raise ValueError(f"expected a list of profiles, received {type(payload).__name__}")

        profile_data = [
            item for item in payload
            if isinstance(item, dict) and item.get("profile") == profile
        ]
        if payload and not profile_data:
            raise ValueError(f"EGD response did not contain profile {profile}")

        readings: list[dict[str, Any]] = []
        units: set[str] = set()
        reported_total = 0
        for item in profile_data:
            data = item.get("data")
            if not isinstance(data, list):
                raise ValueError(f"EGD response for {profile} has no data list")
            readings.extend(record for record in data if isinstance(record, dict))
            if item.get("units"):
                units.add(str(item["units"]).upper())
            if isinstance(item.get("total"), int):
                reported_total += item["total"]

        details: dict[str, Any] = {
            "reading_count": len(readings),
            "api_reported_total": reported_total,
        }
        if not readings:
            details["data_status"] = "No readings returned by EGD"
            details["units"] = next(iter(units), None)
            return None, details

        if len(units) != 1:
            raise ValueError(f"EGD returned missing or inconsistent units for {profile}")
        unit = units.pop()
        if unit == "KW":
            divisor = 4
        elif unit == "KWH":
            divisor = 1
        else:
            raise ValueError(f"Unsupported EGD unit {unit!r} for {profile}")

        try:
            interval_energy = [float(record["value"]) / divisor for record in readings]
        except (KeyError, TypeError, ValueError) as err:
            raise ValueError(f"Invalid reading value in EGD response for {profile}") from err
        value = sum(interval_energy)

        statuses = Counter(
            str(record["status"]) for record in readings if record.get("status")
        )
        details.update(
            {
                "data_status": "Readings received",
                "units": unit,
                "minimum_kwh": min(interval_energy),
                "maximum_kwh": max(interval_energy),
                "status_counts": dict(statuses),
                "first_reading": readings[0].get("timestamp"),
                "last_reading": readings[-1].get("timestamp"),
            }
        )
        return value, details
