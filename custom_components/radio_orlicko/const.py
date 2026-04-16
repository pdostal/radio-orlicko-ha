"""Constants for the Radio Orlicko integration."""

DOMAIN = "radio_orlicko"
PLATFORMS = ["media_player"]

# Radio Orlicko endpoints
API_URL = "https://player.radioorlicko.cz/data/current_song.txt"
PROGRAM_URL = "https://player.radioorlicko.cz/data/program.json"
DEFAULT_STREAM_URL = "https://mediaservice.radioorlicko.cz/stream192.mp3"

# Polling
POLL_INTERVAL = 10            # seconds — same cadence as the official web player
ERROR_RETRY_DELAY = 30        # seconds before retrying after API failure
REQUEST_TIMEOUT = 10          # seconds per HTTP request
PROGRAM_REFRESH_INTERVAL = 3600  # refresh programme schedule once per hour

# Last.fm
LASTFM_API_URL = "https://ws.audioscrobbler.com/2.0/"
CONF_LASTFM_API_KEY = "lastfm_api_key"

# MusicBrainz / Cover Art Archive (fallback album art)
MUSICBRAINZ_API_URL = "https://musicbrainz.org/ws/2/recording/"
COVER_ART_URL = "https://coverartarchive.org/release/{mbid}/front"
MUSICBRAINZ_UA = "radio-orlicko-ha/1.0 (https://github.com/pdostal/radio-orlicko-ha)"
