"""Shared, rate-limited API client and update coordinator."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging
from typing import Any
from zoneinfo import ZoneInfo

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DATA_URL, DOMAIN, TOKEN_URL

_LOGGER = logging.getLogger(__name__)
UPDATE_INTERVAL = timedelta(hours=1)
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=30)


class EGDPowerDataCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Fetch both profiles together once per interval for all entities."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=UPDATE_INTERVAL)
        self.entry = entry
        self.ean: str = entry.data["ean"]
        self.days: int = int(entry.data.get("days", 1))
        self._session = async_get_clientsession(hass)
        self._token: str | None = None
        self._token_expires_at = datetime.min.replace(tzinfo=UTC)

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
            for profile in ("ICC1", "ISC1"):
                async with self._session.get(
                    DATA_URL,
                    headers=headers,
                    params={**params, "profile": profile},
                    timeout=REQUEST_TIMEOUT,
                ) as response:
                    response.raise_for_status()
                    payload = await response.json()
                results[profile] = {
                    "value": self._total_value(payload),
                    "attributes": {
                        "profile": profile,
                        "ean": self.ean,
                        "local_stime": start.strftime("%Y-%m-%d %H:%M:%S %Z%z"),
                        "local_etime": end.strftime("%Y-%m-%d %H:%M:%S %Z%z"),
                        "stime": params["from"],
                        "etime": params["to"],
                    },
                }
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
        expires_in = int(payload.get("expires_in", 300))
        self._token = token
        self._token_expires_at = now + timedelta(seconds=max(0, expires_in - 60))
        return token

    @staticmethod
    def _total_value(payload: Any) -> float:
        """Convert quarter-hour readings to a daily kWh total."""
        try:
            return sum(float(item["value"]) for item in payload[0]["data"]) / 4
        except (IndexError, KeyError, TypeError):
            return 0.0
