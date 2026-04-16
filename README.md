# Radio Orlicko for Home Assistant

[![HACS Custom][hacs-badge]][hacs-url]
[![GitHub Release][release-badge]][release-url]

A [Home Assistant](https://www.home-assistant.io/) custom integration for [Radio Orlicko](https://www.radioorlicko.cz/) — the Czech regional radio station broadcasting from the Orlické hory region.

## Features

- **Media player entity** showing the currently playing artist and song title
- **Elapsed time tracking** — position counter starts from 0 when a new song is detected
- **Current show info** — surfaces the on-air programme name and host as entity attributes
- **Logbook entries** — adds a Home Assistant logbook entry every time the song changes
- **Zero configuration** — just add the integration and it works

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
3. Click **Submit** — no further input required

A `media_player.radio_orlicko` entity will be created immediately.

## Entity Attributes

| Attribute | Description |
|---|---|
| `media_title` | Current song title |
| `media_artist` | Current artist |
| `media_position` | Elapsed seconds since current song started |
| `current_show` | On-air programme name |
| `current_host` | Programme host name(s) |
| `stream_url` | High-quality stream URL (192 kbps MP3) |

## Stream URLs

| Quality | URL |
|---|---|
| High (192 kbps MP3) | `https://mediaservice.radioorlicko.cz/stream192.mp3` |
| Medium (128 kbps MP3) | `https://mediaservice.radioorlicko.cz/stream128.mp3` |
| Low (64 kbps AAC+) | `https://mediaservice.radioorlicko.cz/stream64.aacp` |
| Mobile (32 kbps AAC+) | `https://mediaservice.radioorlicko.cz/stream32.aacp` |

## Notes

- **Progress bar**: Radio Orlicko's API does not expose song duration, so the progress bar shows elapsed time only (no end-point). This is standard behaviour for live radio streams.
- **Polling**: The integration polls the now-playing endpoint every 10 seconds — the same interval used by the official web player.

## License

MIT

---

[hacs-badge]: https://img.shields.io/badge/HACS-Custom-orange.svg
[hacs-url]: https://github.com/hacs/integration
[release-badge]: https://img.shields.io/github/v/release/pdostal/radio-orlicko-ha
[release-url]: https://github.com/pdostal/radio-orlicko-ha/releases
