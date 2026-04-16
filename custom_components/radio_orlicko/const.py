"""Constants for the Radio Orlicko integration."""

DOMAIN = "radio_orlicko"
PLATFORMS = ["media_player"]

API_URL = "https://player.radioorlicko.cz/data/current_song.txt"
PROGRAM_URL = "https://player.radioorlicko.cz/data/program.json"
DEFAULT_STREAM_URL = "https://mediaservice.radioorlicko.cz/stream192.mp3"

POLL_INTERVAL = 10        # seconds — same cadence as the official player
ERROR_RETRY_DELAY = 30    # seconds before retrying after API failure
REQUEST_TIMEOUT = 10      # seconds per HTTP request

PROGRAM_REFRESH_INTERVAL = 3600  # seconds — refresh schedule once per hour
