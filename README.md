# Radio Orlicko for Home Assistant

[![HACS Custom][hacs-badge]][hacs-url]
[![GitHub Release][release-badge]][release-url]

A [Home Assistant](https://www.home-assistant.io/) custom integration for [Radio Orlicko](https://www.radioorlicko.cz/) — the Czech regional radio station broadcasting from the Orlické hory region.

## Companion card

A dedicated Lovelace card for this integration is available at [pdostal/radio-orlicko-ha-card](https://github.com/pdostal/radio-orlicko-ha-card).

## Features

- **Media player entity** showing the currently playing artist and song title
- **Progress bar** — real song duration and elapsed time via Last.fm
- **Album art** — fetched from Last.fm; Cover Art Archive (MusicBrainz) used as fallback
- **Album name, playcount, listener count** — from Last.fm
- **Current show info** — surfaces the on-air programme name and host as entity attributes
- **Logbook entries** — adds a Home Assistant logbook entry every time the song changes

## Installation

### HACS (recommended)

1. Open HACS in your Home Assistant instance
2. Click the three-dot menu → **Custom repositories**
3. Add `https://github.com/pdostal/radio-orlicko-ha` with category **Integration**
4. Search for **Radio Orlicko** and install it
5. Restart Home Assistant

### Manual

1. Download the latest `radio_orlicko.zip` from the [Releases](https://github.com/pdostal/radio-orlicko-ha/releases) page
2. Unzip into your `custom_components/` directory so you have `custom_components/radio_orlicko/`
3. Restart Home Assistant

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Radio Orlicko**
3. Optionally enter a **Last.fm API key** to enable album art and the progress bar
4. Click **Submit**

A `media_player.radio_orlicko` entity will be created immediately.

To add or change the Last.fm API key later: **Settings → Devices & Services → Radio Orlicko → Configure**.

### Getting a Last.fm API key

Register for a free key at [last.fm/api/account/create](https://www.last.fm/api/account/create). The integration works without one, but album art, song duration, and the progress bar will not be available.

## Entity Attributes

| Attribute | Description |
|---|---|
| `media_title` | Current song title |
| `media_artist` | Current artist |
| `media_album_name` | Album name (requires Last.fm key) |
| `media_duration` | Track duration in seconds (requires Last.fm key) |
| `media_position` | Elapsed seconds since current song started |
| `media_image_url` | Album art URL (requires Last.fm key or MusicBrainz match) |
| `current_show` | On-air programme name |
| `current_host` | Programme host name(s) |
| `lastfm_playcount` | Total play count on Last.fm |
| `lastfm_listeners` | Listener count on Last.fm |
| `stream_url` | High-quality stream URL (192 kbps MP3) |

## Stream URLs

| Quality | URL |
|---|---|
| High (192 kbps MP3) | `https://mediaservice.radioorlicko.cz/stream192.mp3` |
| Medium (128 kbps MP3) | `https://mediaservice.radioorlicko.cz/stream128.mp3` |
| Low (64 kbps AAC+) | `https://mediaservice.radioorlicko.cz/stream64.aacp` |
| Mobile (32 kbps AAC+) | `https://mediaservice.radioorlicko.cz/stream32.aacp` |

## Notes

- **Polling**: The integration polls the now-playing endpoint every 10 seconds — the same interval used by the official web player.
- **Progress bar**: Requires a Last.fm API key. Without one, elapsed time is shown but no duration end-point is available.
- **Album art fallback**: If Last.fm has no image for a track, Cover Art Archive (via MusicBrainz) is tried automatically.

## License

MIT

---

[hacs-badge]: https://img.shields.io/badge/HACS-Custom-orange.svg
[hacs-url]: https://github.com/hacs/integration
[release-badge]: https://img.shields.io/github/v/release/pdostal/radio-orlicko-ha
[release-url]: https://github.com/pdostal/radio-orlicko-ha/releases
