from __future__ import annotations

import html
import random
import re
from typing import Any, Dict, List, Tuple

from .tone import is_positiveish_text, extract_year_text


SPORT_CONTEXT_TERMS = [
    "mls", "nfl", "nba", "nhl", "mlb",
    "soccer", "football", "hockey", "basketball", "baseball",
    "playoff", "playoffs", "final", "finals", "cup", "series",
    "season", "match", "goal", "coach", "stadium", "arena", "field",
    "fenway", "gillette", "td garden",
]

DISAMBIGUATION_PATTERNS = {
    "revolution": [
        r"\bnew england revolution\b",
        r"\bne revolution\b",
        r"\brevs\b",
    ],
    "patriots": [
        r"\bnew england patriots\b",
        r"\bpats\b",
        r"\bpatriots\b.*\b(nfl|season|playoff|super bowl|gillette)\b",
        r"\b(nfl|season|playoff|super bowl|gillette)\b.*\bpatriots\b",
    ],
    "celtics": [r"\bboston celtics\b", r"\bceltics\b"],
    "bruins": [r"\bboston bruins\b", r"\bbruins\b"],
    "red sox": [r"\bboston red sox\b", r"\bred sox\b", r"\bfenway\b"],
    "seattle": [r"\bseattle\b", r"\bmariners\b", r"\bseahawks\b", r"\bsounders\b", r"\bkraken\b"],
    "irish": [r"\birish\b", r"\bst\.\s*patrick\b", r"\bst patrick\b", r"\bireland\b", r"\bdublin\b"],
}

ANTI_SPORT_SENSE_TERMS = [
    "french revolution", "american revolution", "revolutionary",
    "uprising", "overthrow", "coup", "guillotine",
]


def _normalize_kw(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _matches_any_regex(text_lower: str, patterns: List[str]) -> bool:
    for pat in patterns:
        if re.search(pat, text_lower, flags=re.IGNORECASE):
            return True
    return False


def _score_sports_relevance(text: str, keywords: List[str]) -> int:
    t = (text or "").strip()
    if not t:
        return -999

    tl = t.lower()

    if not is_positiveish_text(t):
        return -999

    for bad in ANTI_SPORT_SENSE_TERMS:
        if bad in tl:
            return -50

    score = 0

    for w in SPORT_CONTEXT_TERMS:
        if w in tl:
            score += 2

    for raw_kw in (keywords or []):
        kw = _normalize_kw(raw_kw)
        if not kw:
            continue

        if kw in DISAMBIGUATION_PATTERNS:
            if _matches_any_regex(tl, DISAMBIGUATION_PATTERNS[kw]):
                score += 8
            else:
                score -= 3
        else:
            if kw in tl:
                score += 3

    if "boston" in tl or "fenway" in tl or "td garden" in tl or "gillette" in tl:
        score += 4
    if "seattle" in tl:
        score += 2

    if any(x in tl for x in ["won", "champion", "championship", "title", "debut", "opened", "founded", "record"]):
        score += 2

    return score


def generate_card(
    *,
    title: str,
    items: List[Dict[str, Any]],
    keywords: List[str],
    seed: int,
    empty_message: str,
    blurb: str = "",
    n: int = 5,
    show_keywords: bool = True,
) -> str:
    scored: List[Tuple[int, Dict[str, Any]]] = []
    for it in (items or []):
        _, text = extract_year_text(it)
        s = _score_sports_relevance(text, keywords)
        if s <= -100:
            continue
        scored.append((s, it))

    scored.sort(key=lambda x: (x[0], extract_year_text(x[1])[0], extract_year_text(x[1])[1]), reverse=True)

    pool = [it for _, it in scored[:20]]
    if not pool:
        picked: List[Dict[str, Any]] = []
    else:
        rng = random.Random(seed)
        picked = pool if len(pool) <= n else rng.sample(pool, n)

    def li_year_text(items_list: List[Dict[str, Any]]) -> str:
        if not items_list:
            return f"<li><em>{html.escape(empty_message)}</em></li>"
        rows = []
        for it in items_list:
            year, text = extract_year_text(it)
            rows.append(f"<li><span class='year'>{html.escape(year)}</span> {html.escape(text)}</li>")
        return "\n".join(rows)

    kw_line = ""
    if show_keywords and keywords:
        kw_line = (
            f"<div class='sub' style='margin:-6px 0 8px;'>(Filtered by: "
            f"{html.escape(', '.join(keywords[:12]))}{'…' if len(keywords) > 12 else ''})</div>"
        )

    blurb_html = f"<div class='sub' style='margin-top:-2px;'>{html.escape(blurb)}</div>" if blurb else ""

    return f"""
  <section class="card">
    <h2>{html.escape(title)}</h2>
    {blurb_html}
    {kw_line}
    <ul>{li_year_text(picked)}</ul>
  </section>
""".strip()
