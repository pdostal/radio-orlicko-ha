"""Config flow for Radio Orlicko."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    API_URL,
    CONF_LASTFM_API_KEY,
    DOMAIN,
    LASTFM_API_URL,
    REQUEST_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


async def _validate_lastfm_key(session: aiohttp.ClientSession, api_key: str) -> bool:
    """Return True if the Last.fm key is valid (basic check)."""
    try:
        async with session.get(
            LASTFM_API_URL,
            params={
                "method": "auth.getSession",
                "api_key": api_key,
                "format": "json",
            },
            timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
        ) as resp:
            data = await resp.json(content_type=None)
            # Any response other than error code 10 (invalid key) means key is structurally valid
            error = data.get("error")
            return error != 10
    except Exception:  # noqa: BLE001
        return True  # network issue — don't block setup


class RadioOrlickoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Radio Orlicko."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)

            # Verify we can reach Radio Orlicko
            try:
                async with session.get(
                    API_URL,
                    timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
                ) as resp:
                    resp.raise_for_status()
            except (aiohttp.ClientError, TimeoutError):
                errors["base"] = "cannot_connect"

            # Validate Last.fm key if provided
            lastfm_key = user_input.get(CONF_LASTFM_API_KEY, "").strip()
            if lastfm_key and not errors:
                if not await _validate_lastfm_key(session, lastfm_key):
                    errors[CONF_LASTFM_API_KEY] = "invalid_lastfm_key"

            if not errors:
                return self.async_create_entry(
                    title="Radio Orlicko",
                    data={CONF_LASTFM_API_KEY: lastfm_key},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Optional(CONF_LASTFM_API_KEY, default=""): str}
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> RadioOrlickoOptionsFlow:
        """Return the options flow."""
        return RadioOrlickoOptionsFlow(config_entry)


class RadioOrlickoOptionsFlow(config_entries.OptionsFlow):
    """Allow changing the Last.fm API key after setup."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            lastfm_key = user_input.get(CONF_LASTFM_API_KEY, "").strip()
            if lastfm_key:
                if not await _validate_lastfm_key(session, lastfm_key):
                    errors[CONF_LASTFM_API_KEY] = "invalid_lastfm_key"
            if not errors:
                return self.async_create_entry(
                    title="",
                    data={CONF_LASTFM_API_KEY: lastfm_key},
                )

        current_key = self.config_entry.options.get(
            CONF_LASTFM_API_KEY,
            self.config_entry.data.get(CONF_LASTFM_API_KEY, ""),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {vol.Optional(CONF_LASTFM_API_KEY, default=current_key): str}
            ),
            errors=errors,
        )
