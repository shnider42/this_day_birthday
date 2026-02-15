from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple

from .utils import extract_year_text as _extract_year_text  # backward compat import alias


NEGATIVE_HINTS = [
    "war", "battle", "invasion", "massacre", "terror", "terrorist", "attack", "bomb",
    "assassination", "assassinated", "murder", "killing", "killed", "kill", "dead", "crashed", "death", "died", "deadly",
    "execution", "genocide", "riot", "shooting",
    "earthquake", "tsunami", "hurricane", "tornado", "flood", "wildfire", "fire",
    "explosion", "crash", "crashes", "derail", "disaster", "catastrophe",
    "outbreak", "epidemic", "plague", "pandemic", "cholera",
    "arrest", "convicted", "sentenced", "disappear", "police", "disappeared",
]

POSITIVE_HINTS = [
    "won", "win", "wins", "victory", "champion", "championship", "title",
    "founded", "opens", "opened", "launch", "launched",
    "released", "debut", "premiere",
    "first", "record", "breakthrough",
    "discovered", "invented", "created",
    "celebration", "festival", "concert",
]


def is_positiveish_text(text: str) -> bool:
    t = text.lower()
    if any(h in t for h in NEGATIVE_HINTS):
        return False
    return True


def pick_positiveish_item(items: List[Dict[str, Any]], seed: int) -> Optional[Dict[str, Any]]:
    if not items:
        return None
    rng = random.Random(seed)
    good, better = [], []
    for it in items:
        _, txt = extract_year_text(it)
        if not txt:
            continue
        if not is_positiveish_text(txt):
            continue
        good.append(it)
        t = txt.lower()
        if any(h in t for h in POSITIVE_HINTS):
            better.append(it)
    pool = better or good
    return rng.choice(pool) if pool else None


def extract_birth_name(birth_item: Dict[str, Any]) -> str:
    text = str(birth_item.get("text", "")).strip()
    if not text:
        return ""
    return text.split(",", 1)[0].strip()


def extract_year_text(item: Dict[str, Any]) -> Tuple[str, str]:
    year = str(item.get("year", "")).strip()
    text = str(item.get("text", "")).strip()
    return year, text


def pick_famous_birthdays(births: List[Dict[str, Any]], seed: int, n: int = 2) -> List[str]:
    if not births:
        return []
    rng = random.Random(seed + 4242)

    candidates = []
    for b in births:
        _, text = extract_year_text(b)
        if not text:
            continue
        if not is_positiveish_text(text):
            continue
        name = extract_birth_name(b)
        if name:
            candidates.append(name)

    seen = set()
    uniq = []
    for name in candidates:
        key = name.lower()
        if key not in seen:
            seen.add(key)
            uniq.append(name)

    if not uniq:
        return []
    if len(uniq) <= n:
        return uniq
    return rng.sample(uniq, n)
