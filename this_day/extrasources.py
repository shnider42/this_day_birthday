from __future__ import annotations

import datetime as dt
import html
import os
import re
from pathlib import Path
from typing import Any, Dict, List

import requests

from .cache import cache_get, cache_put

# Lightweight optional “extra sources”.
# If any site changes markup, failures are non-fatal (page still loads).

UA = "ThisDayPage/1.0 (family birthday generator)"

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _fetch_html(url: str, timeout: int = 15) -> str:
    r = requests.get(url, headers={"User-Agent": UA}, timeout=timeout)
    r.raise_for_status()
    return r.text


def _strip_tags(s: str) -> str:
    s = html.unescape(s or "")
    s = _TAG_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s).strip()
    return s


def _month_name(month: int) -> str:
    return dt.date(2000, month, 1).strftime("%B").lower()


def _cache_key(prefix: str, month: int, day: int) -> str:
    return f"{prefix}_{month:02d}_{day:02d}"


def thefactsite_day(month: int, day: int, cache_dir: Path) -> Dict[str, Any]:
    """
    Pull a couple items from TheFactSite’s date page:
      - one "Did you know..." fun fact (if found)
      - a small set of "YEAR - event" lines (best-effort)
    """
    ck = _cache_key("thefactsite", month, day)
    cached = cache_get(cache_dir, ck)
    if cached:
        return cached

    mn = _month_name(month)
    url = f"https://www.thefactsite.com/day/{mn}-{day}/"
    out: Dict[str, Any] = {"fun_fact": "", "events": [], "source": "thefactsite", "url": url}

    try:
        raw = _fetch_html(url)

        # Fun fact often contains "Did you know that on this day..."
        m = re.search(r"Did you know that on this day[^<]{0,220}<", raw, flags=re.IGNORECASE)
        if m:
            snippet = raw[m.start() : m.end()]
            out["fun_fact"] = _strip_tags(snippet).rstrip("<").strip()

        # Best-effort "YEAR - ..." lines
        candidates = []
        for mm in re.finditer(r"(\b\d{3,4}\b)\s*[–-]\s*([^<]{20,220})", raw):
            year = mm.group(1).strip()
            text = _strip_tags(mm.group(2))
            if text:
                candidates.append({"year": year, "text": text})
            if len(candidates) >= 12:
                break
        out["events"] = candidates[:10]
    except Exception:
        pass

    cache_put(cache_dir, ck, out)
    return out


def holidays_and_observances_day(month: int, day: int, cache_dir: Path) -> Dict[str, Any]:
    """Pull a short list of daily holidays/observances from holidays-and-observances.com."""
    ck = _cache_key("holidays_observances", month, day)
    cached = cache_get(cache_dir, ck)
    if cached:
        return cached

    mn = _month_name(month)
    url = f"https://www.holidays-and-observances.com/{mn}-{day}.html"
    out: Dict[str, Any] = {"holidays": [], "source": "holidays-and-observances", "url": url}

    try:
        raw = _fetch_html(url)

        # Find a region close to "Daily Holidays ... fall on" to reduce noise.
        anchor = re.search(r"Daily Holidays[^<]{0,140}fall on", raw, flags=re.IGNORECASE)
        region = raw[anchor.start() : anchor.start() + 12000] if anchor else raw[:12000]

        items: List[str] = []
        for mm in re.finditer(r"<li[^>]*>(.*?)</li>", region, flags=re.IGNORECASE | re.DOTALL):
            t = _strip_tags(mm.group(1))
            if not t or len(t) < 3 or len(t) > 140:
                continue
            items.append(t)
            if len(items) >= 18:
                break

        # de-dupe preserving order
        seen = set()
        uniq = []
        for t in items:
            k = t.lower()
            if k in seen:
                continue
            seen.add(k)
            uniq.append(t)

        out["holidays"] = uniq[:14]
    except Exception:
        pass

    cache_put(cache_dir, ck, out)
    return out


def get_extra_sources(month: int, day: int, cache_dir: Path) -> Dict[str, Any]:
    """
    Aggregate optional extra sources.
    Toggle with env vars so Render can enable/disable without code changes:

      EXTRA_THEFACTSITE=1
      EXTRA_HOLIDAYS_OBSERVANCES=1
    """
    use_factsite = os.environ.get("EXTRA_THEFACTSITE", "1").strip().lower() not in {"0", "false", "no"}
    use_holidays = os.environ.get("EXTRA_HOLIDAYS_OBSERVANCES", "1").strip().lower() not in {"0", "false", "no"}

    extras: Dict[str, Any] = {
        "events": [],
        "births": [],
        "holidays": [],
        "fun_facts": [],
        "sources": [],
    }

    if use_factsite:
        fs = thefactsite_day(month, day, cache_dir)
        if fs.get("fun_fact"):
            extras["fun_facts"].append({"text": fs["fun_fact"], "source": fs.get("source", "thefactsite"), "url": fs.get("url", "")})
        for it in (fs.get("events") or []):
            if isinstance(it, dict) and it.get("text"):
                extras["events"].append({
                    "year": str(it.get("year", "—")),
                    "text": str(it.get("text", "")).strip(),
                    "source": fs.get("source", "thefactsite"),
                    "url": fs.get("url", ""),
                })
        extras["sources"].append({"name": "The Fact Site", "url": fs.get("url", "")})

    if use_holidays:
        ho = holidays_and_observances_day(month, day, cache_dir)
        for h in (ho.get("holidays") or []):
            extras["holidays"].append({"text": str(h).strip(), "source": ho.get("source", "holidays-and-observances"), "url": ho.get("url", "")})
        extras["sources"].append({"name": "Holidays-and-Observances", "url": ho.get("url", "")})

    return extras