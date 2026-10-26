"""UI config flow for EGD Power Data."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET

from .const import DOMAIN


class EGDPowerDataConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure EGD portal credentials and EAN."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        """Collect credentials from the Home Assistant UI."""
        if user_input is not None:
            ean = user_input["ean"].strip()
            await self.async_set_unique_id(ean)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"EGD {ean}",
                data={
                    CONF_CLIENT_ID: user_input[CONF_CLIENT_ID].strip(),
                    CONF_CLIENT_SECRET: user_input[CONF_CLIENT_SECRET].strip(),
                    "ean": ean,
                    "days": 1,
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CLIENT_ID): str,
                    vol.Required(CONF_CLIENT_SECRET): str,
                    vol.Required("ean"): str,
                }
            ),
        )
