"""Coordinator for Radio Orlicko."""
from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_URL,
    DOMAIN,
    POLL_INTERVAL,
    PROGRAM_REFRESH_INTERVAL,
    PROGRAM_URL,
    REQUEST_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


def _parse_song(raw: str) -> dict[str, str]:
    """Parse 'Artist - Title' plain text into a dict.

    Falls back gracefully if the separator is absent.
    """
    raw = raw.strip()
    if " - " in raw:
        artist, _, title = raw.partition(" - ")
        return {"artist": artist.strip(), "title": title.strip(), "raw": raw}
    return {"artist": "", "title": raw, "raw": raw}


class RadioOrlickoCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that polls the Radio Orlicko now-playing API."""

    def __init__(self, hass: HomeAssistant, session: aiohttp.ClientSession) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=POLL_INTERVAL),
        )
        self._session = session
        self.song_start_time: datetime | None = None
        self._last_raw: str | None = None
        self._program_cache: dict | None = None
        self._program_fetched_at: datetime | None = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _fetch_text(self, url: str) -> str:
        async with self._session.get(
            url,
            timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
            headers={"Cache-Control": "no-cache"},
        ) as resp:
            resp.raise_for_status()
            return await resp.text()

    async def _fetch_json(self, url: str) -> dict:
        async with self._session.get(
            url,
            timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
            headers={"Cache-Control": "no-cache"},
        ) as resp:
            resp.raise_for_status()
            return await resp.json(content_type=None)

    async def _get_program(self) -> dict | None:
        """Return program schedule, refreshing at most once per hour."""
        now = datetime.now(UTC)
        if self._program_cache is None or (
            self._program_fetched_at is not None
            and (now - self._program_fetched_at).total_seconds() > PROGRAM_REFRESH_INTERVAL
        ):
            try:
                self._program_cache = await self._fetch_json(PROGRAM_URL)
                self._program_fetched_at = now
            except Exception:  # noqa: BLE001
                _LOGGER.debug("Could not fetch program schedule")
        return self._program_cache

    @staticmethod
    def _current_show(program: dict | None) -> tuple[str, str]:
        """Return (show_name, host) for the current day/time, or empty strings."""
        if program is None:
            return "", ""

        now = datetime.now()
        day_key = now.strftime("%A").lower()  # e.g. "monday"
        shows = program.get(day_key, [])

        current_time = now.strftime("%H:%M")
        for show in shows:
            if show.get("start", "") <= current_time < show.get("end", ""):
                return show.get("show", ""), show.get("host", "")

        return "", ""

    # ------------------------------------------------------------------
    # DataUpdateCoordinator protocol
    # ------------------------------------------------------------------

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch current song and program data."""
        try:
            raw = await self._fetch_text(API_URL)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Error fetching Radio Orlicko data: {err}") from err

        song = _parse_song(raw)

        # Track when this song started
        if song["raw"] != self._last_raw:
            self.song_start_time = datetime.now(UTC)
            self._last_raw = song["raw"]

        program = await self._get_program()
        current_show, current_host = self._current_show(program)

        return {
            "artist": song["artist"],
            "title": song["title"],
            "raw": song["raw"],
            "song_start_time": self.song_start_time,
            "current_show": current_show,
            "current_host": current_host,
        }

    def async_shutdown(self) -> None:
        """Clean up resources."""
