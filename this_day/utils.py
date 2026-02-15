from __future__ import annotations

import datetime as dt
import re
from typing import Any, List, Tuple


def parse_mm_dd(s: str) -> Tuple[int, int]:
    m = re.fullmatch(r"\s*(\d{1,2})-(\d{1,2})\s*", s)
    if not m:
        raise ValueError("Date must be in MM-DD format, e.g. 12-18")
    month = int(m.group(1))
    day = int(m.group(2))
    _ = dt.date(2000, month, day)  # validate
    return month, day


def today_mm_dd() -> Tuple[int, int]:
    t = dt.date.today()
    return t.month, t.day


def safe_int(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except Exception:
        return default


def ends_with_punct(s: str) -> bool:
    return s.strip().endswith((".", "!", "?"))


def sentence(s: str) -> str:
    s = s.strip()
    if not s:
        return s
    return s if ends_with_punct(s) else (s + ".")


def normalize_phone(s: str) -> str:
    digits = "".join(ch for ch in s if ch.isdigit())
    if len(digits) == 10:
        return f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"
    return s.strip()


def join_names_nicely(names: List[str]) -> str:
    names = [n.strip() for n in names if n.strip()]
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return ", ".join(names[:-1]) + f", and {names[-1]}"


from typing import Any, Dict, Tuple

def extract_year_text(item: Dict[str, Any]) -> Tuple[str, str]:
    year = str(item.get("year", "")).strip()
    text = str(item.get("text", "")).strip()
    return year, text
