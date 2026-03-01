from __future__ import annotations

import argparse
from pathlib import Path

from .app import app
from .birthdays import build_birthday_index, birthdays_for_date, load_birthdays, people_to_phone_list
from .config import (
    DEFAULT_BIRTHDAYS,
    DEFAULT_CACHE_DIR,
    DEFAULT_OUT,
    DEFAULT_ROCK_KEYWORDS,
    DEFAULT_SPORTS_KEYWORDS,
    DEFAULT_SUBTITLE,
    DEFAULT_TITLE,
)
from .fetchers import numbersapi_fun_fact, wiki_on_this_day
from .extrasources import get_extra_sources
from .renderer import html_page
from .utils import parse_mm_dd, today_mm_dd


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Generate a fun 'This Day' webpage (family birthday edition).")
    p.add_argument("--date", help="Date in MM-DD (default: today).")
    p.add_argument("--out", default=DEFAULT_OUT, help=f"Output HTML filename (default: {DEFAULT_OUT}).")
    p.add_argument("--birthdays", default=DEFAULT_BIRTHDAYS, help=f"Path to birthdays.json (default: {DEFAULT_BIRTHDAYS}).")
    p.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR, help=f"Cache directory (default: {DEFAULT_CACHE_DIR}).")
    p.add_argument("--title", default=DEFAULT_TITLE, help="Page title.")
    p.add_argument("--subtitle", default=DEFAULT_SUBTITLE, help="Page subtitle.")
    p.add_argument("--sports-keywords", default=",".join(DEFAULT_SPORTS_KEYWORDS))
    p.add_argument("--rock-keywords", default=",".join(DEFAULT_ROCK_KEYWORDS))
    p.add_argument("--serve", action="store_true", help="Run a local web server (requires APP_USER/APP_PASS env vars).")
    p.add_argument("--port", type=int, default=5000)
    p.add_argument("--show", action="store_true", help="When exporting static HTML, include facts immediately (no gating).")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.serve:
        app.run(host="0.0.0.0", port=args.port, debug=False)
        return 0

    if args.date:
        month, day = parse_mm_dd(args.date)
    else:
        month, day = today_mm_dd()

    sports_keywords = [k.strip() for k in args.sports_keywords.split(",") if k.strip()] or DEFAULT_SPORTS_KEYWORDS
    rock_keywords = [k.strip() for k in args.rock_keywords.split(",") if k.strip()] or DEFAULT_ROCK_KEYWORDS

    birthdays_path = Path(args.birthdays)
    cache_dir = Path(args.cache_dir)

    birthdays = load_birthdays(birthdays_path)
    birthday_hits = birthdays_for_date(birthdays, month, day)
    phones = people_to_phone_list(birthdays)
    bday_index = build_birthday_index(birthdays)

    seed = int(f"{month:02d}{day:02d}")

    onthisday = {"events": [], "births": []}
    fun_fact = ""
    extras = {}

    show_facts = bool(args.show)

    if show_facts:
        onthisday = wiki_on_this_day(month, day, cache_dir)
        fun_fact = numbersapi_fun_fact(month, day, cache_dir)
        extras = get_extra_sources(month, day, cache_dir)

    page = html_page(
        title=args.title,
        subtitle=args.subtitle,
        month=month,
        day=day,
        onthisday=onthisday,
        fun_fact=fun_fact,
        extras=extras,
        birthday_hits=birthday_hits,
        phones=phones,
        sports_keywords=sports_keywords,
        rock_keywords=rock_keywords,
        seed=seed,
        birthdays_index=bday_index,
        show_facts=show_facts,
    )

    out_path = Path(args.out)
    out_path.write_text(page, encoding="utf-8")
    print(f"[ok] Wrote {out_path.resolve()}")
    return 0
