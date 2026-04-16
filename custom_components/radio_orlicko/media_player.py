"""Media player entity for Radio Orlicko."""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from homeassistant.components.logbook import (
    EVENT_LOGBOOK_ENTRY,
    LOGBOOK_ENTRY_DOMAIN,
    LOGBOOK_ENTRY_ENTITY_ID,
    LOGBOOK_ENTRY_MESSAGE,
    LOGBOOK_ENTRY_NAME,
)
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
    _attr_name = None
    _attr_media_content_type = MediaType.MUSIC
    _attr_state = MediaPlayerState.PLAYING
    _attr_supported_features = MediaPlayerEntityFeature(0)
    _attr_media_content_id = DEFAULT_STREAM_URL

    def __init__(self, coordinator: RadioOrlickoCoordinator) -> None:
        """Initialise the media player."""
        super().__init__(coordinator)
        self._attr_unique_id = DOMAIN
        self._attr_device_info = {
            "identifiers": {(DOMAIN, DOMAIN)},
            "name": "Radio Orlicko",
            "manufacturer": "Radio Orlicko",
            "model": "Online Stream",
            "configuration_url": "https://www.radioorlicko.cz",
        }
        self._last_raw: str | None = None

    # ------------------------------------------------------------------
    # CoordinatorEntity callbacks
    # ------------------------------------------------------------------

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from coordinator and fire logbook on song change."""
        data = self.coordinator.data
        if data is None:
            return

        raw = data.get("raw", "")
        if raw and raw != self._last_raw:
            if self._last_raw is not None:
                # Fire a logbook entry — first update after initial load doesn't count
                title = data.get("title", "")
                artist = data.get("artist", "")
                message = f"Now playing: {title} by {artist}" if artist else f"Now playing: {title}"
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
        """Return the current track title."""
        if self.coordinator.data:
            return self.coordinator.data.get("title") or None
        return None

    @property
    def media_artist(self) -> str | None:
        """Return the current artist."""
        if self.coordinator.data:
            return self.coordinator.data.get("artist") or None
        return None

    @property
    def media_duration(self) -> float | None:
        """Duration is unknown for a live stream."""
        return None

    @property
    def media_position(self) -> float | None:
        """Return elapsed seconds since the current song started."""
        if self.coordinator.data is None:
            return None
        start = self.coordinator.data.get("song_start_time")
        if start is None:
            return None
        elapsed = (datetime.now(UTC) - start).total_seconds()
        return max(0.0, elapsed)

    @property
    def media_position_updated_at(self) -> datetime | None:
        """Return when the position was last calculated (now, for interpolation)."""
        if self.coordinator.last_update_success_time is None:
            return None
        return self.coordinator.last_update_success_time

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes including the current show."""
        if self.coordinator.data is None:
            return {}
        return {
            "current_show": self.coordinator.data.get("current_show", ""),
            "current_host": self.coordinator.data.get("current_host", ""),
            "stream_url": DEFAULT_STREAM_URL,
        }
