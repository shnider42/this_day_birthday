from __future__ import annotations

import random
from typing import Any, Dict, List

from .tone import pick_positiveish_item, pick_famous_birthdays, extract_year_text
from .utils import join_names_nicely, sentence


def make_sms_summary(
    *,
    date_label: str,
    fun_fact: str,
    featured_events: List[Dict[str, Any]],
    bostonish_featured: List[Dict[str, Any]],
    rock_featured: List[Dict[str, Any]],
    birthday_hits: List[Dict[str, Any]],
    famous_bdays: List[str],
    seed: int,
) -> str:
    rng = random.Random(seed + 999)

    headline_it = pick_positiveish_item(featured_events, seed + 1)
    sports_it = pick_positiveish_item(bostonish_featured, seed + 2)
    rock_it = pick_positiveish_item(rock_featured, seed + 3)

    openers = [
        f"🎉 Hear ye, hear ye: it’s {date_label} and the vibes are birthday-shaped.",
        f"✨ Family bulletin! {date_label} just walked in wearing confetti and demanding cake.",
        f"🎈Okay team: {date_label} fun facts incoming — helmets optional, joy required.",
        f"💌 A cheerful {date_label} dispatch from the ‘this day’ department of whimsy (now with extra sparkle).",
    ]
    s1 = sentence(rng.choice(openers))

    if headline_it:
        y, t = extract_year_text(headline_it)
        s2 = sentence(f"On this day in {y}: {t}")
    else:
        s2 = sentence("On this day in history: something interesting definitely happened, and we’re choosing to focus on the sparkle")

    s3 = sentence(f"Did you know? {fun_fact.strip()}")

    extras: List[str] = []
    if sports_it:
        y, t = extract_year_text(sports_it)
        extras.append(sentence(f"🏟️ Boston sports corner: {y} — {t}"))
    if rock_it:
        y, t = extract_year_text(rock_it)
        extras.append(sentence(f"🎸 Classic rock time machine: {y} — {t}"))

    if famous_bdays:
        extras.append(sentence(f"⭐ Famous birthday roll call: {join_names_nicely(famous_bdays)} share this date too"))
        extras.append(sentence("So yes, today’s theme is: ‘legendary company, acceptable levels of chaos.’"))

    rituals = [
        "Today’s tiny mission: send one nice text, eat one good snack, and do one dramatic “ta-da!” for no reason.",
        "Birthday protocol: deploy emojis, deliver compliments, and do not let the cake-to-fun ratio fall below 1:1.",
        "Your assignment (should you choose to accept it): be kind, be goofy, and pretend you’re in a celebratory montage.",
        "Mandatory holiday for the soul: laugh once, hype someone up, and consider a second dessert purely on principle.",
    ]
    s4 = sentence(rng.choice(rituals))

    if birthday_hits:
        names = [str(x.get("name", "someone")).strip() for x in birthday_hits]
        names_joined = join_names_nicely(names)

        bday_lines = [
            f"🎂 And MOST importantly: happy birthday to {names_joined}! May your day be fun, your cake be generous, and your group chat be appropriately chaotic.",
            f"🥳 Birthday alert for {names_joined}! Wishing you big laughs, good food, and absolutely zero responsibilities (except enjoying yourself).",
            f"🎉 It’s {names_joined}’s birthday! Everyone send love, memes, and possibly a ridiculous amount of cake emojis. 🎂🎂🎂",
            f"🎈 Today we celebrate {names_joined}! Hope your day is a highlight reel and your year is even better.",
        ]
        s5 = sentence(rng.choice(bday_lines))
        s6 = sentence("Everybody say happy birthday right now (yes, even the lurkers) 🎊")
    else:
        s5 = sentence("And if it’s secretly your birthday and you didn’t tell us… congrats on the stealth mission. 😄")
        s6 = sentence("Still: you deserve a cookie for surviving today. 🍪")

    signoffs = [
        "Love you all — now go forth and be delightful.",
        "End of bulletin. Please celebrate responsibly (or at least enthusiastically).",
        "This message was brought to you by the Spirit of Patti™ and the Department of Good Vibes.",
        "Alright, that’s the report. Somebody cue the birthday playlist!",
    ]
    s7 = sentence(rng.choice(signoffs))

    parts = [s1, s2, s3]
    parts.extend(extras)
    parts.extend([s4, s5, s6, s7])
    return " ".join(p.strip() for p in parts if p.strip())
