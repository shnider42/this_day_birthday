from __future__ import annotations

import datetime as dt
import random
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from .cache import cache_get, cache_put
from .config import NUMBERSAPI_DATE, WIKIMEDIA_ONTHISDAY


def fetch_json(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 15) -> Dict[str, Any]:
    r = requests.get(url, headers=headers or {}, timeout=timeout)
    r.raise_for_status()
    return r.json()


def wiki_on_this_day(month: int, day: int, cache_dir: Path) -> Dict[str, Any]:
    cache_key = f"wikimedia_onthisday_{month:02d}_{day:02d}"
    cached = cache_get(cache_dir, cache_key)
    if cached:
        return cached

    headers = {"User-Agent": "ThisDayPage/1.0 (family birthday generator)"}
    url = WIKIMEDIA_ONTHISDAY.format(month=month, day=day)
    data = fetch_json(url, headers=headers)
    cache_put(cache_dir, cache_key, data)
    return data


def fallback_fun_fact(month: int, day: int) -> str:
    date = dt.date(2000, month, day)
    day_of_year = int(date.strftime("%j"))
    date_label = date.strftime("%B %d").replace(" 0", " ")
    days_left = 365 - day_of_year

    options = [
        f"{date_label} is day #{day_of_year} of the year — which means we’re {day_of_year} days into this year’s nonsense (and excellence).",
        f"On {date_label}, the calendar is basically shouting “main character energy” — use it responsibly.",
        f"Fun calendar magic: {date_label} happens exactly once per year. Statistically rare. Emotionally elite.",
        "Did you know? The best birthdays tend to land on days that end in “today.” Science-ish.",
        f"{date_label} is the {day_of_year}th page in this year’s 365-page adventure novel.",
        f"If the year were a playlist, {date_label} would be track #{day_of_year}. No skips allowed.",
        f"{date_label}: {day_of_year} days down, {days_left} to go. Pace yourself.",
        f"Legend has it that {date_label} was invented specifically for good vibes.",
        f"{date_label} has a 100% historical accuracy rate of definitely existing.",
        f"On this day ({date_label}), at least one person dramatically said, “This is my moment.”",
        f"{date_label} is mathematically guaranteed to be somebody’s favorite day.",
        f"{date_label} ranks in the top 365 days of the year. Impressive stuff.",
        f"Fun fact: {date_label} has been quietly showing up every year without missing a shift.",
        f"{date_label} — proof that time is moving and we are moving with it (ideally forward).",
        f"{date_label} is a limited-edition date. Collect responsibly.",
        f"If today had a flavor, {date_label} would taste like optimism with a hint of chaos.",
        f"{date_label} is the universe’s subtle reminder to hydrate and text someone back.",
        f"Somewhere in history, {date_label} was absolutely unforgettable.",
        f"{date_label} is day #{day_of_year}. That’s a lot of commitment from the calendar.",
        f"Breaking news: {date_label} has entered the chat.",
        f"{date_label} comes with complimentary potential. Supplies are unlimited.",
        f"If every day had a mascot, {date_label} would be holding confetti.",
        f"{date_label}: not just a date — a vibe.",
        f"On {date_label}, the odds of something mildly interesting happening are extremely high.",
        f"{date_label} is proof that the Earth has successfully completed {day_of_year} daily rotations this year.",
        f"{date_label} has historically been associated with doing your best (or at least trying).",
        f"{date_label} is a solid choice for making a small but dramatic declaration.",
        f"Fun stat: {date_label} is exactly 24 hours long. Efficiency.",
        f"{date_label} is the kind of day that appreciates a bold snack decision.",
        f"{date_label} once inspired someone to say, “Why not?”",
        f"{date_label}: a strong contender for “Most Likely to Be Remembered Fondly.”",
        f"If days earned badges, {date_label} would have at least three.",
        f"{date_label} has been quietly building lore since the beginning of calendars.",
        f"{date_label} — because the other 364 days needed competition.",
        f"Today’s headline: {date_label} refuses to be average.",
        f"{date_label} is statistically tied with every other day for importance — but feels special anyway.",
        f"{date_label}: a perfectly valid excuse to celebrate something.",
        f"{date_label} is a reminder that we’ve made it {day_of_year} steps into the year. Nicely done.",
        f"{date_label} is a calendar cameo with full-screen energy.",
        f"If the year were a staircase, {date_label} is step #{day_of_year}. Keep climbing.",
        f"{date_label} pairs well with ambition and a decent playlist.",
        f"{date_label}: built on history, powered by caffeine.",
        f"On {date_label}, the universe briefly considered adding fireworks. Still under review.",
        f"{date_label} has strong “start something small but meaningful” energy.",
        f"{date_label} exists so that future-you can say, “Remember that day?”",
        f"{date_label} is one of only 365 chances this year to make a random Tuesday legendary.",
        f"{date_label}: highly recommended by 9 out of 10 calendars.",
        f"{date_label} comes preloaded with potential plot twists.",
        f"{date_label} is an excellent day for bold declarations or quiet wins.",
        f"{date_label} has a documented history of being exactly on time.",
        f"{date_label}: the calendar’s way of saying, “Keep going.”",
        f"Fun calendar trivia: {date_label} is uniquely positioned between yesterday and tomorrow. Strategic.",
        f"{date_label} — because every epic year needs a chapter #{day_of_year}.",
    ]

    return random.choice(options)


def numbersapi_fun_fact(month: int, day: int, cache_dir: Path) -> str:
    cache_key = f"numbersapi_{month:02d}_{day:02d}"
    cached = cache_get(cache_dir, cache_key)
    if cached and isinstance(cached.get("text"), str) and cached["text"].strip():
        return cached["text"].strip()

    try:
        url = NUMBERSAPI_DATE.format(month=month, day=day)
        data = fetch_json(url)
        cache_put(cache_dir, cache_key, data)
        text = str(data.get("text", "")).strip()
        if text:
            return text
    except Exception:
        pass

    return fallback_fun_fact(month, day)
