"""Media player entity for Radio Orlicko."""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_STREAM_URL, DOMAIN
from .coordinator import RadioOrlickoCoordinator

_LOGGER = logging.getLogger(__name__)

# Logbook constants — defined locally to avoid import-order issues with
# homeassistant.components.logbook not yet loaded at integration startup.
EVENT_LOGBOOK_ENTRY = "logbook_entry"
LOGBOOK_ENTRY_NAME = "name"
LOGBOOK_ENTRY_MESSAGE = "message"
LOGBOOK_ENTRY_DOMAIN = "domain"
LOGBOOK_ENTRY_ENTITY_ID = "entity_id"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Radio Orlicko media player from a config entry."""
    coordinator: RadioOrlickoCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RadioOrlickoMediaPlayer(coordinator)])


class RadioOrlickoMediaPlayer(CoordinatorEntity[RadioOrlickoCoordinator], MediaPlayerEntity):
    """Representation of the Radio Orlicko live stream."""

    _attr_has_entity_name = True
    _attr_name = "Radio Orlicko"
    _attr_icon = "mdi:radio"
    _attr_media_content_type = MediaType.MUSIC
    _attr_supported_features = MediaPlayerEntityFeature(0)
    _attr_media_content_id = DEFAULT_STREAM_URL

    def __init__(self, coordinator: RadioOrlickoCoordinator) -> None:
        """Initialise the media player."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_media_player"
        self._last_raw: str | None = None

    async def async_added_to_hass(self) -> None:
        """Stamp position timestamp on boot so the elapsed counter works immediately."""
        await super().async_added_to_hass()
        self._attr_media_position_updated_at = self.coordinator.last_update_success_time
        self.async_write_ha_state()

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    @property
    def state(self) -> MediaPlayerState:
        """Always playing — live radio stream."""
        return MediaPlayerState.PLAYING

    # ------------------------------------------------------------------
    # CoordinatorEntity callbacks
    # ------------------------------------------------------------------

    @callback
    def _handle_coordinator_update(self) -> None:
        """Stamp position timestamp and fire logbook entry on song change."""
        self._attr_media_position_updated_at = self.coordinator.last_update_success_time

        data = self.coordinator.data
        if data is not None:
            raw = data.get("raw", "")
            if raw and raw != self._last_raw:
                if self._last_raw is not None:
                    title = data.get("title", "")
                    artist = data.get("artist", "")
                    message = (
                        f"Now playing: {title} by {artist}"
                        if artist
                        else f"Now playing: {title}"
                    )
                    self.hass.bus.async_fire(
                        EVENT_LOGBOOK_ENTRY,
                        {
                            LOGBOOK_ENTRY_NAME: "Radio Orlicko",
                            LOGBOOK_ENTRY_MESSAGE: message,
                            LOGBOOK_ENTRY_DOMAIN: DOMAIN,
                            LOGBOOK_ENTRY_ENTITY_ID: self.entity_id,
                        },
                    )
                self._last_raw = raw

        super()._handle_coordinator_update()

    # ------------------------------------------------------------------
    # Media player properties
    # ------------------------------------------------------------------

    @property
    def media_title(self) -> str | None:
        """Current track title."""
        if self.coordinator.data:
            return self.coordinator.data.get("title") or None
        return None

    @property
    def media_artist(self) -> str | None:
        """Current artist."""
        if self.coordinator.data:
            return self.coordinator.data.get("artist") or None
        return None

    @property
    def media_album_name(self) -> str | None:
        """Album name from Last.fm."""
        if self.coordinator.data:
            return self.coordinator.data.get("album") or None
        return None

    @property
    def media_duration(self) -> float | None:
        """Track duration in seconds from Last.fm (enables progress bar)."""
        if self.coordinator.data:
            return self.coordinator.data.get("duration")
        return None

    @property
    def media_position(self) -> float | None:
        """Elapsed seconds since the current song was first detected."""
        if self.coordinator.data is None:
            return None
        start = self.coordinator.data.get("song_start_time")
        if start is None:
            return None
        return max(0.0, (datetime.now(UTC) - start).total_seconds())

    @property
    def media_image_url(self) -> str | None:
        """Album art URL from Last.fm or Cover Art Archive."""
        if self.coordinator.data:
            return self.coordinator.data.get("image_url") or None
        return None

    @property
    def media_image_remotely_accessible(self) -> bool:
        """Album art is hosted on a public CDN."""
        return True

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Extra attributes including show info and Last.fm stats."""
        if self.coordinator.data is None:
            return {}
        d = self.coordinator.data
        attrs: dict[str, Any] = {
            "stream_url": DEFAULT_STREAM_URL,
        }
        if d.get("current_show"):
            attrs["current_show"] = d["current_show"]
        if d.get("current_host"):
            attrs["current_host"] = d["current_host"]
        if d.get("playcount"):
            attrs["lastfm_playcount"] = d["playcount"]
        if d.get("listeners"):
            attrs["lastfm_listeners"] = d["listeners"]
        return attrs
