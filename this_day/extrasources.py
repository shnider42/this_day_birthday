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

    Hardened parsing:
      - avoid matching random numbers from HTML/CSS/JS
      - only accept plausible years and sentence-like text
      - try list-item parsing first; regex is fallback
    """
    ck = _cache_key("thefactsite", month, day)
    cached = cache_get(cache_dir, ck)
    if cached:
        return cached

    mn = _month_name(month)
    url = f"https://www.thefactsite.com/day/{mn}-{day}/"
    out: Dict[str, Any] = {"fun_fact": "", "events": [], "source": "The Fact Site", "url": url}

    def looks_like_event_text(t: str) -> bool:
        if not t:
            return False
        t = t.strip()

        # Must contain letters (not just numbers/punctuation)
        if not re.search(r"[A-Za-z]", t):
            return False

        # Reject text that is mostly digits/punct
        non_space = re.sub(r"\s+", "", t)
        if not non_space:
            return False
        digitish = sum(1 for ch in non_space if ch.isdigit() or ch in "-–—:/.,()[]#")
        if digitish / max(1, len(non_space)) > 0.65:
            return False

        # Avoid very short junk
        if len(t) < 25:
            return False

        return True

    def year_ok(y: str) -> bool:
        try:
            yi = int(y)
        except Exception:
            return False
        current_year = dt.date.today().year
        return 1000 <= yi <= current_year

    try:
        raw = _fetch_html(url)

        # Fun fact: try to find a "Did you know..." sentence
        m = re.search(r"(Did you know[^<]{20,240})<", raw, flags=re.IGNORECASE)
        if m:
            out["fun_fact"] = _strip_tags(m.group(1)).strip()

        events: List[Dict[str, str]] = []

        # 1) Preferred: parse <li> items that contain a bold/strong year
        # Look for list items where a 3-4 digit year appears in <strong> or <b>
        for mm in re.finditer(r"<li[^>]*>(.*?)</li>", raw, flags=re.IGNORECASE | re.DOTALL):
            li_html = mm.group(1)

            # Extract a year that is explicitly emphasized
            ym = re.search(r"<(strong|b)[^>]*>\s*(\d{3,4})\s*</\1>", li_html, flags=re.IGNORECASE)
            if not ym:
                continue

            year = ym.group(2).strip()
            if not year_ok(year):
                continue

            # Remove the emphasized year from the li and strip tags
            li_wo_year = re.sub(r"<(strong|b)[^>]*>\s*\d{3,4}\s*</\1>", " ", li_html, flags=re.IGNORECASE)
            text = _strip_tags(li_wo_year)

            # Sometimes the site uses separators like "-" or "–" after the year
            text = re.sub(r"^\s*[-–—:]\s*", "", text).strip()

            if not looks_like_event_text(text):
                continue

            events.append({"year": year, "text": text})
            if len(events) >= 10:
                break

        # 2) Fallback: regex "YEAR - something" but hardened
        if not events:
            for mm in re.finditer(r"\b(\d{3,4})\b\s{0,3}[–-]\s{0,3}([^<]{25,240})", raw):
                year = mm.group(1).strip()
                if not year_ok(year):
                    continue

                text = _strip_tags(mm.group(2)).strip()
                if not looks_like_event_text(text):
                    continue

                events.append({"year": year, "text": text})
                if len(events) >= 10:
                    break

        # De-dupe by (year, text)
        seen = set()
        deduped = []
        for e in events:
            k = (e.get("year", "").strip(), e.get("text", "").strip().lower())
            if not k[0] or not k[1] or k in seen:
                continue
            seen.add(k)
            deduped.append(e)

        out["events"] = deduped[:10]

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