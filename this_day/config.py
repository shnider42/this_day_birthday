from __future__ import annotations

# Constants & defaults

WIKIMEDIA_ONTHISDAY = (
    "https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/all/{month:02d}/{day:02d}"
)
NUMBERSAPI_DATE = "https://numbersapi.com/{month}/{day}/date?json"

DEFAULT_SPORTS_KEYWORDS = [
    "Boston", "Red Sox", "Celtics", "Bruins", "Patriots", "Revolution",
    "Fenway", "TD Garden", "Gillette", "New England",
]

DEFAULT_ROCK_KEYWORDS = [
    "album", "single", "released", "release", "chart", "Billboard", "concert", "tour", "festival",
    "recorded", "recording", "debut", "hit", "band", "rock",
    "The Beatles", "Beatles", "Rolling Stones", "Stones", "Led Zeppelin", "Zeppelin",
    "Pink Floyd", "Floyd", "The Who", "Queen", "David Bowie", "Bowie",
    "Elton John", "AC/DC", "Aerosmith", "Bruce Springsteen", "Springsteen",
    "Tom Petty", "Nirvana", "Fleetwood Mac", "The Doors", "Jimi Hendrix", "Hendrix",
]

DEFAULT_TITLE = "Patti’s This Day Fun Facts"
DEFAULT_SUBTITLE = "History, sports-ish chaos, classic rock vibes, and family birthdays."
DEFAULT_OUT = "this_day.html"
DEFAULT_BIRTHDAYS = "birthdays.json"
DEFAULT_CACHE_DIR = ".cache_this_day"
