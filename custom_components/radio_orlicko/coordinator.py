"""Coordinator for Radio Orlicko."""
from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import quote

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    TimestampDataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    API_URL,
    CONF_LASTFM_API_KEY,
    COVER_ART_URL,
    DOMAIN,
    LASTFM_API_URL,
    MUSICBRAINZ_API_URL,
    MUSICBRAINZ_UA,
    POLL_INTERVAL,
    PROGRAM_REFRESH_INTERVAL,
    PROGRAM_URL,
    REQUEST_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


def _parse_song(raw: str) -> dict[str, str]:
    """Parse 'Artist - Title' plain text into a dict."""
    raw = raw.strip()
    if " - " in raw:
        artist, _, title = raw.partition(" - ")
        return {"artist": artist.strip(), "title": title.strip(), "raw": raw}
    return {"artist": "", "title": raw, "raw": raw}


class RadioOrlickoCoordinator(TimestampDataUpdateCoordinator[dict[str, Any]]):
    """Polls Radio Orlicko every 10 s and enriches song data via Last.fm / MusicBrainz."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        lastfm_api_key: str = "",
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=POLL_INTERVAL),
        )
        self._session = session
        self.lastfm_api_key = lastfm_api_key

        self.song_start_time: datetime | None = None
        self._last_raw: str | None = None

        # Enriched metadata cached per song (keyed by raw song string)
        self._enriched_cache: dict[str, dict] = {}

        self._program_cache: dict | None = None
        self._program_fetched_at: datetime | None = None

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    async def _get_text(self, url: str, **kwargs: Any) -> str:
        async with self._session.get(
            url,
            timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
            headers={"Cache-Control": "no-cache"},
            **kwargs,
        ) as resp:
            resp.raise_for_status()
            return await resp.text()

    async def _get_json(self, url: str, **kwargs: Any) -> dict:
        async with self._session.get(
            url,
            timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
            headers={"Cache-Control": "no-cache"},
            **kwargs,
        ) as resp:
            resp.raise_for_status()
            return await resp.json(content_type=None)

    # ------------------------------------------------------------------
    # Last.fm enrichment
    # ------------------------------------------------------------------

    async def _fetch_lastfm(self, artist: str, title: str) -> dict:
        """Fetch track info from Last.fm. Returns {} on any failure."""
        if not self.lastfm_api_key or not artist or not title:
            return {}
        try:
            data = await self._get_json(
                LASTFM_API_URL,
                params={
                    "method": "track.getInfo",
                    "api_key": self.lastfm_api_key,
                    "artist": artist,
                    "track": title,
                    "autocorrect": "1",
                    "format": "json",
                },
            )
        except Exception:  # noqa: BLE001
            _LOGGER.debug("Last.fm fetch failed for '%s – %s'", artist, title)
            return {}

        track = data.get("track", {})
        if not track or "error" in data:
            return {}

        # Duration: Last.fm returns milliseconds as a string (or "0")
        duration_ms = int(track.get("duration") or 0)
        duration_s = duration_ms / 1000 if duration_ms > 0 else None

        # Album art — pick the largest available image
        images = track.get("album", {}).get("image", [])
        image_url = ""
        for img in reversed(images):
            url = img.get("#text", "")
            if url:
                image_url = url
                break

        return {
            "duration": duration_s,
            "album": track.get("album", {}).get("title", ""),
            "image_url": image_url,
            "playcount": track.get("playcount", ""),
            "listeners": track.get("listeners", ""),
        }

    # ------------------------------------------------------------------
    # MusicBrainz / Cover Art Archive (fallback album art)
    # ------------------------------------------------------------------

    async def _fetch_musicbrainz_art(self, artist: str, title: str) -> str:
        """Try to get album art from Cover Art Archive via MusicBrainz. Returns URL or ''."""
        if not artist or not title:
            return ""
        try:
            mb_data = await self._get_json(
                MUSICBRAINZ_API_URL,
                params={
                    "query": f'artist:"{artist}" AND recording:"{title}"',
                    "fmt": "json",
                    "limit": "1",
                },
                headers={
                    "User-Agent": MUSICBRAINZ_UA,
                    "Cache-Control": "no-cache",
                },
            )
        except Exception:  # noqa: BLE001
            _LOGGER.debug("MusicBrainz fetch failed for '%s – %s'", artist, title)
            return ""

        recordings = mb_data.get("recordings", [])
        if not recordings:
            return ""

        # Find the first release with a valid MBID
        releases = recordings[0].get("releases", [])
        for release in releases:
            mbid = release.get("id", "")
            if not mbid:
                continue
            try:
                # Cover Art Archive returns a 307 redirect to the actual image
                url = COVER_ART_URL.format(mbid=mbid)
                async with self._session.head(
                    url,
                    timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
                    allow_redirects=True,
                ) as resp:
                    if resp.status < 400:
                        return str(resp.url)
            except Exception:  # noqa: BLE001
                continue

        return ""

    # ------------------------------------------------------------------
    # Enrichment orchestration
    # ------------------------------------------------------------------

    async def _enrich(self, artist: str, title: str) -> dict:
        """Return enriched metadata for the current song (cached per song)."""
        raw_key = f"{artist} - {title}"
        if raw_key in self._enriched_cache:
            return self._enriched_cache[raw_key]

        result: dict[str, Any] = {
            "duration": None,
            "album": "",
            "image_url": "",
            "playcount": "",
            "listeners": "",
        }

        # Try Last.fm first
        lfm = await self._fetch_lastfm(artist, title)
        result.update({k: v for k, v in lfm.items() if v})

        # Fall back to MusicBrainz for album art if Last.fm had none
        if not result["image_url"]:
            mb_art = await self._fetch_musicbrainz_art(artist, title)
            if mb_art:
                result["image_url"] = mb_art

        self._enriched_cache[raw_key] = result
        return result

    # ------------------------------------------------------------------
    # Programme schedule
    # ------------------------------------------------------------------

    async def _get_program(self) -> dict | None:
        now = datetime.now(UTC)
        if self._program_cache is None or (
            self._program_fetched_at is not None
            and (now - self._program_fetched_at).total_seconds() > PROGRAM_REFRESH_INTERVAL
        ):
            try:
                self._program_cache = await self._get_json(PROGRAM_URL)
                self._program_fetched_at = now
            except Exception:  # noqa: BLE001
                _LOGGER.debug("Could not fetch Radio Orlicko programme schedule")
        return self._program_cache

    @staticmethod
    def _current_show(program: dict | None) -> tuple[str, str]:
        if program is None:
            return "", ""
        now = datetime.now()
        day_key = now.strftime("%A").lower()
        current_time = now.strftime("%H:%M")
        for show in program.get(day_key, []):
            if show.get("start", "") <= current_time < show.get("end", ""):
                return show.get("show", ""), show.get("host", "")
        return "", ""

    # ------------------------------------------------------------------
    # DataUpdateCoordinator protocol
    # ------------------------------------------------------------------

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch current song, enrich via Last.fm/MusicBrainz, return combined data."""
        try:
            raw = await self._get_text(API_URL)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Error fetching Radio Orlicko data: {err}") from err

        song = _parse_song(raw)

        # Track song start time
        if song["raw"] != self._last_raw:
            self.song_start_time = datetime.now(UTC)
            self._last_raw = song["raw"]

        # Enrich with Last.fm / MusicBrainz (only fires actual HTTP on song change)
        enriched = await self._enrich(song["artist"], song["title"])

        program = await self._get_program()
        current_show, current_host = self._current_show(program)

        return {
            "artist": song["artist"],
            "title": song["title"],
            "raw": song["raw"],
            "song_start_time": self.song_start_time,
            "duration": enriched["duration"],
            "album": enriched["album"],
            "image_url": enriched["image_url"],
            "playcount": enriched["playcount"],
            "listeners": enriched["listeners"],
            "current_show": current_show,
            "current_host": current_host,
        }

    async def async_shutdown(self) -> None:
        """Clean up on integration unload."""
        await super().async_shutdown()
