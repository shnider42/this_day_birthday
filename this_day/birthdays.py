from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .utils import normalize_phone, safe_int


def ensure_birthdays_file(path: Path) -> None:
    if path.exists():
        return
    template = [
        {
            "name": "Patti",
            "month": 5,
            "day": 14,
            "relation": "Mom",
            "note": "Chief Fun Fact Officer",
            "phone": "000-000-0000",
        },
    ]
    path.write_text(json.dumps(template, ensure_ascii=False, indent=2), encoding="utf-8")


def load_birthdays(path: Path) -> List[Dict[str, Any]]:
    ensure_birthdays_file(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("birthdays.json must contain a JSON array of entries.")
    for item in data:
        if isinstance(item, dict) and item.get("phone"):
            item["phone"] = normalize_phone(str(item.get("phone", "")).strip())
    return data


def birthdays_for_date(birthdays: List[Dict[str, Any]], month: int, day: int) -> List[Dict[str, Any]]:
    hits = []
    for b in birthdays:
        if safe_int(b.get("month")) == month and safe_int(b.get("day")) == day:
            hits.append(b)

    def sort_key(x: Dict[str, Any]) -> str:
        name = str(x.get("name", "")).strip()
        parts = name.split()
        last = parts[-1] if parts else ""
        return f"{last}|{name}".lower()

    return sorted(hits, key=sort_key)


def people_to_phone_list(birthdays: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    for b in birthdays:
        if not isinstance(b, dict):
            continue
        phone = normalize_phone(str(b.get("phone", "")).strip())
        if not phone:
            continue
        label = str(b.get("name", "")).strip()
        out.append({"phone": phone, "label": label})

    # de-dupe by digits
    seen = set()
    uniq = []
    for p in out:
        d = "".join(ch for ch in p["phone"] if ch.isdigit())
        if d and d not in seen:
            seen.add(d)
            uniq.append(p)
    return uniq


def phones_to_to_field_text(phones: List[Dict[str, str]]) -> str:
    nums = [p.get("phone", "").strip() for p in phones if p.get("phone", "").strip()]
    return ", ".join(nums)


def build_birthday_index(birthdays: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    idx: Dict[str, List[str]] = {}
    for b in birthdays:
        m = safe_int(b.get("month"))
        d = safe_int(b.get("day"))
        if m <= 0 or d <= 0 or m > 12 or d > 31:
            continue
        key = f"{m:02d}-{d:02d}"
        name = str(b.get("name", "")).strip()
        if not name:
            continue
        idx.setdefault(key, []).append(name)

    for k in list(idx.keys()):
        idx[k] = sorted(idx[k], key=lambda s: s.lower())
    return idx


def filter_phones_excluding_birthday_people(
    phones: List[Dict[str, str]],
    birthday_hits: List[Dict[str, Any]],
) -> List[Dict[str, str]]:
    exclude_digits = set()
    for h in birthday_hits:
        p = str(h.get("phone", "")).strip()
        if not p:
            continue
        exclude_digits.add("".join(ch for ch in p if ch.isdigit()))

    if not exclude_digits:
        return phones

    kept: List[Dict[str, str]] = []
    for item in phones:
        p = str(item.get("phone", "")).strip()
        digits = "".join(ch for ch in p if ch.isdigit())
        if digits and digits in exclude_digits:
            continue
        kept.append(item)
    return kept
