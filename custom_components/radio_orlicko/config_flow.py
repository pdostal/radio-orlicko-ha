"""Config flow for Radio Orlicko."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API_URL, DOMAIN, REQUEST_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class RadioOrlickoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Radio Orlicko."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            try:
                async with session.get(
                    API_URL, timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
                ) as resp:
                    resp.raise_for_status()
            except (aiohttp.ClientError, TimeoutError):
                return self.async_show_form(
                    step_id="user",
                    errors={"base": "cannot_connect"},
                )

            return self.async_create_entry(title="Radio Orlicko", data={})

        return self.async_show_form(step_id="user")
