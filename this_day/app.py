from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, Response, request

from .auth import basic_auth_required
from .birthdays import (
    build_birthday_index,
    birthdays_for_date,
    filter_phones_excluding_birthday_people,
    load_birthdays,
    people_to_phone_list,
)
from .config import (
    DEFAULT_BIRTHDAYS,
    DEFAULT_CACHE_DIR,
    DEFAULT_ROCK_KEYWORDS,
    DEFAULT_SPORTS_KEYWORDS,
    DEFAULT_SUBTITLE,
    DEFAULT_TITLE,
)
from .fetchers import numbersapi_fun_fact, wiki_on_this_day
from .renderer import html_page
from .utils import parse_mm_dd, today_mm_dd


app = Flask(__name__)


@app.get("/")
def render_page() -> Response:
    auth_resp = basic_auth_required()
    if auth_resp:
        return auth_resp

    birthdays_path = Path(os.environ.get("BIRTHDAYS_FILE", DEFAULT_BIRTHDAYS))
    cache_dir = Path(os.environ.get("CACHE_DIR", DEFAULT_CACHE_DIR))
    title = os.environ.get("PAGE_TITLE", DEFAULT_TITLE)
    subtitle = os.environ.get("PAGE_SUBTITLE", DEFAULT_SUBTITLE)

    show = request.args.get("show", "").strip()
    show_facts = (show == "1" or show.lower() in {"true", "yes", "y"})

    qdate = request.args.get("date", "").strip()
    try:
        if qdate:
            month, day = parse_mm_dd(qdate)
        else:
            month, day = today_mm_dd()
    except ValueError as e:
        return Response(str(e), status=400, mimetype="text/plain")

    sports_keywords = [
        k.strip()
        for k in os.environ.get("SPORTS_KEYWORDS", ",".join(DEFAULT_SPORTS_KEYWORDS)).split(",")
        if k.strip()
    ]
    rock_keywords = [
        k.strip()
        for k in os.environ.get("ROCK_KEYWORDS", ",".join(DEFAULT_ROCK_KEYWORDS)).split(",")
        if k.strip()
    ]

    birthdays = load_birthdays(birthdays_path)
    birthday_hits = birthdays_for_date(birthdays, month, day)

    phones = people_to_phone_list(birthdays)
    if show_facts:
        phones = filter_phones_excluding_birthday_people(phones, birthday_hits)

    bday_index = build_birthday_index(birthdays)

    seed = int(f"{month:02d}{day:02d}")

    onthisday = {"events": [], "births": []}
    fun_fact = ""
    debug_error = ""

    if show_facts:
        try:
            onthisday = wiki_on_this_day(month, day, cache_dir)
        except Exception as e:
            onthisday = {"events": [], "births": []}
            debug_error = f"Wikimedia fetch failed: {type(e).__name__}: {e}"

        try:
            fun_fact = numbersapi_fun_fact(month, day, cache_dir)
        except Exception as e:
            fun_fact = ""
            debug_error = (debug_error + " | " if debug_error else "") + f"NumbersAPI failed: {type(e).__name__}: {e}"

    page = html_page(
        title=title,
        subtitle=subtitle,
        month=month,
        day=day,
        onthisday=onthisday,
        fun_fact=fun_fact,
        birthday_hits=birthday_hits,
        phones=phones,
        sports_keywords=sports_keywords,
        rock_keywords=rock_keywords,
        seed=seed,
        birthdays_index=bday_index,
        show_facts=show_facts,
        debug_error=debug_error,
    )
    return Response(page, mimetype="text/html")
