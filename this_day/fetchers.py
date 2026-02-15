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
    options = [
        f"{date_label} is day #{day_of_year} of the year — which means we’re {day_of_year} days into this year’s nonsense (and excellence).",
        f"On {date_label}, the calendar is basically shouting “main character energy” — use it responsibly.",
        f"Fun calendar magic: {date_label} happens exactly once per year. Statistically rare. Emotionally elite.",
        "Did you know? The best birthdays tend to land on days that end in “today.” Science-ish.",
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
