from __future__ import annotations

import datetime as dt
import html
import json
import random
from typing import Any, Dict, List, Tuple

from .birthdays import phones_to_to_field_text
from .cards import generate_card
from .sms import make_sms_summary
from .tone import pick_famous_birthdays, extract_year_text
from .utils import join_names_nicely, sentence


def pick_items(items: List[Dict[str, Any]], n: int, seed: int) -> List[Dict[str, Any]]:
    if not items:
        return []
    rng = random.Random(seed)
    if len(items) <= n:
        return items
    return rng.sample(items, n)


def filter_keywords(items: List[Dict[str, Any]], keywords: List[str]) -> List[Dict[str, Any]]:
    out = []
    for it in items:
        _, text = extract_year_text(it)
        t = text.lower()
        if any(k.lower() in t for k in keywords):
            out.append(it)
    return out


def html_page(
    *,
    title: str,
    subtitle: str,
    month: int,
    day: int,
    onthisday: Dict[str, Any],
    fun_fact: str,
    birthday_hits: List[Dict[str, str]],
    phones: List[Tuple[str, str]],
    sports_keywords: List[str],
    rock_keywords: List[str],
    seed: int,
    birthdays_index: Dict[Tuple[int, int], List[str]],
    show_facts: bool,
    debug_error: str = "",
    extras: Dict[str, Any] | None = None,
) -> str:
    date_label = dt.date(2000, month, day).strftime("%B %d").replace(" 0", " ")

    events = (onthisday.get("events", []) or []) if show_facts else []
    births = (onthisday.get("births", []) or []) if show_facts else []

    extras = extras or {}

    extra_events = (extras.get("events") or []) if show_facts else []
    extra_births = (extras.get("births") or []) if show_facts else []
    extra_holidays = (extras.get("holidays") or []) if show_facts else []

    if extra_events:
        events = list(events) + list(extra_events)

    if extra_births:
        births = list(births) + list(extra_births)

    featured_events = pick_items(events, n=6, seed=seed + 1) if show_facts else []
    featured_births = pick_items(births, n=6, seed=seed + 2) if show_facts else []

    bostonish_all = filter_keywords(events, sports_keywords) if show_facts else []
    bostonish_featured = pick_items(bostonish_all, n=5, seed=seed + 4) if show_facts else []

    rockish_all = filter_keywords(events, rock_keywords) if show_facts else []
    rockish_featured = pick_items(rockish_all, n=5, seed=seed + 5) if show_facts else []

    famous_bdays_summary = pick_famous_birthdays(births, seed=seed, n=2) if show_facts else []
    famous_bdays_card = pick_famous_birthdays(births, seed=seed + 7, n=6) if show_facts else []

    sms_summary = ""
    if show_facts:
        sms_summary = make_sms_summary(
            date_label=date_label,
            fun_fact=fun_fact,
            featured_events=featured_events,
            bostonish_featured=bostonish_featured,
            rock_featured=rockish_featured,
            birthday_hits=birthday_hits,
            famous_bdays=famous_bdays_summary,
            seed=seed,
        )

    to_field_text = phones_to_to_field_text(phones)

    def li_year_text(items_list: List[Dict[str, Any]]) -> str:
        if not items_list:
            return "<li><em>Nothing to show here (or the internet gremlins intervened).</em></li>"
        rows = []
        for it in items_list:
            year, text = extract_year_text(it)
            src = str(it.get("source", "")).strip() if isinstance(it, dict) else ""
            if src:
                text = f"{text} — {src}"
            rows.append(f"<li><span class='year'>{html.escape(year)}</span> {html.escape(text)}</li>")
        return "\n".join(rows)

    def famous_bday_list(names: List[str]) -> str:
        if not names:
            return "<div class='sub' style='margin-top:8px;'><em>No famous birthdays surfaced today — which means the family gets the spotlight. 😄</em></div>"
        items = "".join(f"<li>{html.escape(n)}</li>" for n in names)
        return f"""
          <div class="sub" style="margin-top:10px;">⭐ <strong>Famous birthdays</strong> (aka “you’re in good company”):</div>
          <ul style="margin-top:6px;">{items}</ul>
          <div class="sub" style="margin-top:6px;">If any of these are your favorite, you’re allowed to claim “same birthday energy.”</div>
        """

    def birthday_block(hits: List[Dict[str, Any]]) -> str:
        if not hits:
            return "<p><em>No family birthdays listed for this date (yet).</em></p>"
        cards = []
        for h in hits:
            name = html.escape(str(h.get("name", "Someone Awesome")))
            relation = str(h.get("relation", "")).strip()
            relation_html = f"<div class='meta'>{html.escape(relation)}</div>" if relation else ""
            note = str(h.get("note", "")).strip()
            note_html = f"<div class='note'>{html.escape(note)}</div>" if note else ""
            phone = str(h.get("phone", "")).strip()
            phone_html = f"<div class='meta'>📱 {html.escape(phone)}</div>" if phone else ""
            cards.append(
                f"""
                <div class="bday-card">
                  <div class="bday-name">🎂 {name}</div>
                  {relation_html}
                  {phone_html}
                  {note_html}
                </div>
                """
            )
        return "\n".join(cards)

    if birthday_hits:
        names = [str(x.get("name", "someone")).strip() for x in birthday_hits]
        closer = f"And also, {join_names_nicely(names)} {'was' if len(names) == 1 else 'were'} born on this day. Everybody say happy birthday! 🎉"
    else:
        closer = "And also: if someone in the family was born on this day, add them to birthdays.json and I’ll start bragging about it. 😄"

    css = _CSS
    js = _JS

    def fonts_link_tag() -> str:
        return (
            '<link rel="preconnect" href="https://fonts.googleapis.com">'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            '<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Fraunces:opsz,wght@9..144,400..700&family=Inter:wght@400;600;800&display=swap" rel="stylesheet">'
        )

    view_year = dt.date.today().year
    view_month = month
    selected_obj = {"year": view_year, "month": month, "day": day}

    if not show_facts:
        t = dt.date.today()
        view_year = t.year
        view_month = t.month
        selected_obj = {"year": t.year, "month": t.month, "day": t.day}

    bday_index_json = json.dumps(birthdays_index, ensure_ascii=False)
    init_json = json.dumps(
        {"viewYear": view_year, "viewMonth": view_month, "selected": selected_obj},
        ensure_ascii=False,
    )

    facts_html = ""
    sms_html = ""
    if show_facts:
        rng_cards = random.Random(seed + 2024)

        phone_card = f"""
  <section class="card">
    <div class="to-title">📲 Copy/Paste Phone List (for iMessage “To:”)</div>
    <textarea id="toText" class="to-text" readonly>{html.escape(to_field_text)}</textarea>
    <div class="sms-actions">
      <button class="btn" onclick="copyToList()">Copy</button>
      <span id="copyToStatus" class="hint"></span>
      <span class="hint">Tip: paste into a new iMessage “To:” field (comma-separated).</span>
    </div>
  </section>
"""

        family_card = f"""
  <section class="card">
    <h2>🎂 Family birthdays</h2>
    <div class="sub" style="margin-top:-2px;">Today’s official job: hype the birthday humans. 🎉</div>
    {birthday_block(birthday_hits)}
    {famous_bday_list(famous_bdays_card)}
    <div class="closer">{html.escape(closer)}</div>
  </section>
"""

        history_card = f"""
  <section class="card">
    <h2>📜 On this day in history</h2>
    <ul>{li_year_text(featured_events)}</ul>
  </section>
"""

        boston_card = generate_card(
            title="🏟️ Boston & friends sports corner",
            items=events,
            keywords=sports_keywords,
            seed=seed + 404,
            blurb="Sports-first, good-vibes-only. If a word has two meanings, we pick the jersey version.",
            empty_message="No obvious sports hits today — the universe is in a bye week. 😄",
            n=5,
            show_keywords=True,
        )

        rock_card = f"""
  <section class="card">
    <h2>🎸 This day in classic rock history</h2>
    <div class="sub" style="margin:-6px 0 8px;">(Filtered by: {html.escape(", ".join(rock_keywords[:10]))}{'…' if len(rock_keywords) > 10 else ''})</div>
    <ul>{li_year_text(rockish_featured)}</ul>
    {"<div class='sub' style='margin-top:8px;'><em>No rock hits found today — add more keywords and we’ll summon them. 🎶</em></div>" if not rockish_all else ""}
  </section>
"""

        funfact_card = f"""
  <section class="card">
    <h2>🧠 Did you know?</h2>
    <div class="funfact">{html.escape(fun_fact)}</div>
  </section>
"""

        births_card = f"""
  <section class="card">
    <h2>👶 Notable births</h2>
    <ul>{li_year_text(featured_births)}</ul>
  </section>
"""

        prompts = [
            "Send one nice text to someone you love — bonus points for a ridiculous emoji combo.",
            "Do a tiny act of kindness (hold a door, compliment someone, or share snacks like a champion).",
            "Put on ONE song that makes you feel like the main character and dramatically strut to it for 20 seconds.",
            "Try a ‘two-minute tidy’ in one small spot — then celebrate like you cleaned the whole house.",
            "Ask someone a fun question: “What’s your most random talent?” and enjoy the answers.",
            "Take a picture of something pretty today (sky, pet, coffee, whatever) and declare it ✨art✨.",
            "Quick nostalgia mission: name a happy memory from your childhood and share it with someone.",
            "Wholesome chaos: tell somebody you appreciate them, then immediately change the subject like a spy.",
        ]
        if birthday_hits:
            names = [str(x.get("name", "")).strip() for x in birthday_hits if str(x.get("name", "")).strip()]
            who = join_names_nicely(names) if names else "the birthday human"
            prompts.insert(0, f"Birthday mission: send {who} one compliment and one meme. (In that order.)")

        wildcard_text = sentence(rng_cards.choice(prompts))
        wildcard_card = f"""
  <section class="card">
    <h2>🎯 Tiny mission of the day</h2>
    <div class="funfact">{html.escape(wildcard_text)}</div>
    <div class="sub" style="margin-top:10px;">Optional: if you do it, you’re allowed to say “nailed it” out loud.</div>
  </section>
"""

        holidays_card = ""
        if extra_holidays:
            items = []
            for h in extra_holidays[:10]:
                t = str(h.get("text", "")).strip() if isinstance(h, dict) else str(h).strip()
                if t:
                    items.append(f"<li>{html.escape(t)}</li>")

            if items:
                holidays_card = f"""
        <section class="card">
          <h2>🎉 Holidays & observances</h2>
          <div class="sub" style="margin-top:-2px;">
            Extra: pulled from a holiday calendar source.
          </div>
          <ul>
            {''.join(items)}
          </ul>
        </section>
        """

        pool = [family_card, history_card, boston_card, rock_card, funfact_card, births_card, wildcard_card]
        if holidays_card:
            pool.append(holidays_card)
        chosen = rng_cards.sample(pool, k=5) if len(pool) >= 5 else pool[:]

        final_cards = [phone_card] + chosen
        rng_cards.shuffle(final_cards)

        delayed = []
        for i, c in enumerate(final_cards):
            delayed.append(c.replace('class="card"', f'class="card" style="animation-delay: {i*55}ms;"', 1))
        facts_html = "<main>\n" + "\n".join(delayed) + "\n</main>\n"

        sms_html = f"""
  <div class="sms-wrap">
    <div class="sms-card">
      <div class="sms-title">📩 Copy/Paste Text Message</div>
      <textarea id="smsText" class="sms-text" readonly>{html.escape(sms_summary)}</textarea>
      <div class="sms-actions">
        <button class="btn" onclick="copySms()">Copy</button>
        <span id="copyStatus" class="hint"></span>
        <span class="hint">Positive-only-ish summary: avoids darker events when composing this paragraph.</span>
      </div>
    </div>
  </div>
"""
    else:
        facts_html = """
  <main>
    <section class="card">
      <h2>🗓️ Ready when you are</h2>
      <div class="sub">Pick a date on the mini calendar and hit <strong>Generate</strong>. This page intentionally waits so it doesn’t spam-load everything at once.</div>
      <div class="sub" style="margin-top:8px;">Tip: birthdays are highlighted. Click one for instant “today’s mission.”</div>
    </section>
  </main>
"""

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)} — {html.escape(date_label)}</title>
  {fonts_link_tag()}
  <style>{css}</style>
</head>
<body>
  <header>
    <div class="hero">
      <h1>{html.escape(title)} <span style="color:var(--muted);font-weight:500;">— {html.escape(date_label if show_facts else "Pick a date")}</span></h1>
      <div class="hero-date">{html.escape(subtitle)}</div>

      <div class="badges">
        <div class="badge sox">Red Sox</div>
        <div class="badge celtics">Celtics</div>
        <div class="badge bruins">Bruins</div>
        <div class="badge pats">Patriots</div>
        <div class="badge">Family birthdays 🎂</div>
      </div>
    </div>
  </header>

  <div class="sub" style="margin-top:8px;">
    <span style="opacity:.85">debug:</span>
        date=<strong>{month:02d}-{day:02d}</strong>,
        show=<strong>{"1" if show_facts else "0"}</strong>,
        events=<strong>{len(onthisday.get("events", []) or [])}</strong>,
        births=<strong>{len(onthisday.get("births", []) or [])}</strong>
        {f"<div style='margin-top:6px;color:#ffb81c;'>{html.escape(debug_error)}</div>" if debug_error else ""}
  </div>

  <div class="top-strip">
    <div></div>
    <section class="card" style="animation-delay: 60ms;">
      <div class="cal-head">
        <div class="cal-title" id="calTitle">Month YYYY</div>
        <div class="cal-nav">
          <button class="iconbtn" id="calPrev" aria-label="Previous month">‹</button>
          <button class="iconbtn" id="calNext" aria-label="Next month">›</button>
        </div>
      </div>

      <table class="calendar">
        <thead>
          <tr id="calHeadRow"></tr>
        </thead>
        <tbody id="calBody"></tbody>
      </table>

      <div class="cal-controls">
        <button class="btn" id="calGenerateBtn" disabled>Generate</button>
        <div>
          <div class="cal-selected" id="calSelectedLabel">Pick a day to generate the fun facts.</div>
          <div class="hint" id="calGenerateHint"></div>
        </div>
      </div>
    </section>
  </div>

  {facts_html}

  {sms_html}

  <footer>
    Sources: Wikimedia “On this day” feed + Numbers API (with a cheerful fallback). Generated by <code>this_day</code>.
  </footer>

  <script>
    window.__BDAY_INDEX__ = {bday_index_json};
    window.__INIT__ = {init_json};
  </script>
  <script>{js}</script>
</body>
</html>
"""


# CSS and JS kept as big literals to avoid mixing concerns in renderer logic.
_CSS = r""":root{
  --font-hero: "Bebas Neue", ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
  --font-body: "Inter", ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
  --font-sms: "Fraunces", ui-serif, Georgia, "Times New Roman", serif;

  --bg:#0b1220;
  --card:#111b2e;
  --text:#e8edf7;
  --muted:#a7b4cc;

  --sox-red:#BD3039;
  --sox-navy:#0C2340;

  --celtics:#007A33;
  --bruins:#FFB81C;
  --pats-navy:#002244;
  --pats-red:#C60C30;

  --accent: color-mix(in srgb, var(--bruins) 55%, var(--sox-red) 45%);
  --accent2: color-mix(in srgb, var(--celtics) 55%, var(--pats-red) 45%);

  --scrollY: 0px;
}

*{ box-sizing:border-box; }
html,body{ height:100%; }
body{
  margin:0;
  font-family: var(--font-body);
  color:var(--text);
  background: var(--bg);
  overflow-x:hidden;
}

body::before{
  content:"";
  position:fixed;
  inset:-20vh -20vw;
  z-index:-3;
  background:
    radial-gradient(900px 480px at 18% 8%, rgba(120,220,232,0.12) 0%, rgba(11,18,32,0) 60%),
    radial-gradient(700px 420px at 88% 10%, rgba(255,184,28,0.10) 0%, rgba(11,18,32,0) 60%),
    radial-gradient(650px 420px at 20% 96%, rgba(189,48,57,0.10) 0%, rgba(11,18,32,0) 60%),
    radial-gradient(850px 520px at 78% 92%, rgba(0,122,51,0.10) 0%, rgba(11,18,32,0) 60%),
    linear-gradient(180deg, #0b1220 0%, #0b1220 100%);
  transform: translateY(calc(var(--scrollY) * -0.06)) scale(1.03);
  filter: saturate(1.05) contrast(1.05);
}

header{
  padding: 34px 20px 14px;
  max-width: 1040px;
  margin: 0 auto;
  position:relative;
}
.hero{
  border-radius: 22px;
  padding: 22px 20px 18px;
  border: 1px solid rgba(255,255,255,0.10);
  background:
    linear-gradient(135deg,
      rgba(17,27,46,0.92) 0%,
      rgba(17,27,46,0.74) 45%,
      rgba(17,27,46,0.90) 100%);
  box-shadow: 0 18px 50px rgba(0,0,0,0.45);
  overflow:hidden;
}
.hero::before{
  content:"";
  position:absolute;
  inset:-40%;
  background:
    radial-gradient(closest-side at 30% 40%, rgba(255,184,28,0.16), rgba(0,0,0,0) 60%),
    radial-gradient(closest-side at 75% 55%, rgba(189,48,57,0.14), rgba(0,0,0,0) 62%),
    radial-gradient(closest-side at 45% 95%, rgba(0,122,51,0.14), rgba(0,0,0,0) 64%);
  transform: translateY(calc(var(--scrollY) * -0.04)) rotate(-6deg);
  pointer-events:none;
}
h1{
  margin:0;
  font-family: var(--font-hero);
  font-size: 46px;
  letter-spacing: 0.7px;
  line-height: 1.0;
}
.hero-date{
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--muted);
  margin-top: 8px;
}
.sub{
  margin-top: 10px;
  color: var(--muted);
  font-size: 15px;
  line-height: 1.35;
}
.badges{
  display:flex;
  flex-wrap:wrap;
  gap:10px;
  margin-top: 14px;
}
.badge{
  font-size:12px;
  color: rgba(232,237,247,0.95);
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid rgba(255,255,255,0.10);
  background: rgba(255,255,255,0.06);
  backdrop-filter: blur(6px);
}
.badge.sox{ border-color: rgba(189,48,57,0.45); }
.badge.celtics{ border-color: rgba(0,122,51,0.45); }
.badge.bruins{ border-color: rgba(255,184,28,0.45); }
.badge.pats{ border-color: rgba(0,34,68,0.55); }

.top-strip{
  max-width: 1040px;
  margin: 0 auto;
  padding: 0 20px 6px;
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
}
@media (min-width: 960px){
  .top-strip{ grid-template-columns: 1.15fr 0.85fr; }
}

main{
  max-width: 1040px;
  margin: 0 auto;
  padding: 10px 20px 24px;
  display: grid;
  gap: 14px;
  grid-template-columns: 1fr;
}
@media (min-width: 960px){
  main { grid-template-columns: 1.15fr 0.85fr; }
}

.card{
  position:relative;
  background: color-mix(in srgb, var(--card) 92%, black 8%);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 18px;
  padding: 16px 16px 14px;
  box-shadow: 0 12px 34px rgba(0,0,0,0.35);
  transform: translateY(10px);
  opacity: 0;
  animation: cardIn 650ms ease forwards;
}
@keyframes cardIn{ to { transform: translateY(0); opacity: 1; } }

.card:hover{
  transform: translateY(-4px);
  box-shadow: 0 18px 44px rgba(0,0,0,0.45);
  border-color: rgba(255,255,255,0.14);
  transition: transform 140ms ease, box-shadow 140ms ease, border-color 140ms ease;
}

h2{
  margin: 0 0 10px;
  font-size: 18px;
  color: var(--accent);
  letter-spacing: 0.2px;
}
h2::after{
  content:"";
  display:block;
  height:2px;
  width: 54px;
  margin-top: 8px;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--accent), rgba(120,220,232,0));
  opacity: 0.9;
}

ul{ margin:0; padding-left:18px; }
li{ margin: 8px 0; line-height: 1.35; }
.year{
  display:inline-block;
  min-width: 54px;
  color: var(--muted);
}
.funfact{
  font-size: 16px;
  line-height: 1.45;
  color: #f3f7ff;
}

.bday-card{
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 14px;
  padding: 12px;
  margin: 10px 0;
}
.bday-name{ font-weight: 750; font-size: 16px; }
.meta{ color: var(--muted); margin-top: 4px; }
.note{ margin-top: 6px; color: #d9e4ff; }
.closer{
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(255,255,255,0.08);
  color: #f6fbff;
}

.to-title{
  color: var(--accent2);
  font-weight: 800;
  margin: 0 0 10px;
  font-size: 16px;
}
.to-text{
  width: 100%;
  min-height: 90px;
  resize: vertical;
  border-radius: 14px;
  border: 1px solid rgba(255,255,255,0.14);
  background: rgba(0,0,0,0.18);
  color: var(--text);
  padding: 14px;
  line-height: 1.45;
  font-size: 15px;
  font-family: var(--font-body);
}

.sms-wrap{ max-width: 1040px; margin: 0 auto; padding: 0 20px 44px; }
.sms-card{
  background: rgba(255,255,255,0.07);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 18px;
  padding: 16px;
  box-shadow: 0 16px 44px rgba(0,0,0,0.42);
  position:relative;
  overflow:hidden;
}
.sms-card::before{
  content:"";
  position:absolute;
  inset:-40%;
  background:
    radial-gradient(closest-side at 20% 30%, rgba(255,184,28,0.20), rgba(0,0,0,0) 60%),
    radial-gradient(closest-side at 85% 45%, rgba(189,48,57,0.18), rgba(0,0,0,0) 62%),
    radial-gradient(closest-side at 45% 95%, rgba(0,122,51,0.18), rgba(0,0,0,0) 64%);
  transform: translateY(calc(var(--scrollY) * -0.03));
  pointer-events:none;
  opacity: 0.9;
}
.sms-title{
  color: var(--accent2);
  font-weight: 800;
  margin: 0 0 10px;
  font-size: 16px;
  position:relative;
}
.sms-text{
  width: 100%;
  min-height: 200px;
  resize: vertical;
  border-radius: 14px;
  border: 1px solid rgba(255,255,255,0.14);
  background: rgba(0,0,0,0.18);
  color: var(--text);
  padding: 14px;
  line-height: 1.5;
  font-size: 15px;
  font-family: var(--font-sms);
  position:relative;
}
.sms-actions{
  margin-top: 10px;
  display:flex;
  gap:10px;
  align-items:center;
  flex-wrap:wrap;
  position:relative;
}
.btn{
  border: 1px solid rgba(255,255,255,0.16);
  background: rgba(255,255,255,0.09);
  color: var(--text);
  padding: 9px 12px;
  border-radius: 12px;
  cursor: pointer;
}
.btn:hover{ background: rgba(255,255,255,0.13); }
.hint{ color: var(--muted); font-size: 12px; }

footer{
  max-width: 1040px;
  margin: 0 auto;
  padding: 10px 20px 30px;
  color: var(--muted);
  font-size: 12px;
}
code{ color: #c7f0ff; }

.cal-head{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:10px;
}
.cal-title{
  font-weight: 800;
  color: var(--accent2);
  letter-spacing: 0.2px;
}
.cal-nav{
  display:flex;
  gap:8px;
}
.iconbtn{
  width: 34px;
  height: 34px;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.16);
  background: rgba(255,255,255,0.08);
  color: var(--text);
  cursor:pointer;
  display:flex;
  align-items:center;
  justify-content:center;
}
.iconbtn:hover{ background: rgba(255,255,255,0.12); }

.calendar{
  margin-top: 10px;
  width:100%;
  border-collapse: collapse;
}
.calendar th{
  text-align:center;
  font-size: 12px;
  color: var(--muted);
  padding: 6px 0;
}
.calendar td{
  padding: 0;
}
.cal-day{
  width: 100%;
  height: 36px;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.06);
  background: rgba(0,0,0,0.12);
  color: var(--text);
  cursor:pointer;
  display:flex;
  align-items:center;
  justify-content:center;
  margin: 3px 0;
  user-select:none;
  position:relative;
}
.cal-day:hover{
  background: rgba(255,255,255,0.10);
  border-color: rgba(255,255,255,0.12);
}
.cal-day.muted{
  opacity: 0.35;
  cursor: default;
}
.cal-day.today{
  outline: 2px solid rgba(120,220,232,0.45);
}
.cal-day.has-bday{
  background: color-mix(in srgb, rgba(189,48,57,0.22) 50%, rgba(255,184,28,0.16) 50%);
  border-color: rgba(255,184,28,0.35);
}
.cal-day.selected{
  outline: 2px solid rgba(255,184,28,0.55);
}
.cal-dot{
  position:absolute;
  bottom: 6px;
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: rgba(255,184,28,0.85);
  box-shadow: 0 0 10px rgba(255,184,28,0.35);
}

.cal-controls{
  margin-top: 10px;
  display:flex;
  gap:10px;
  align-items:center;
  flex-wrap: wrap;
}
.cal-selected{
  color: var(--muted);
  font-size: 13px;
}
"""
_JS = r"""function copyTextArea(id, statusId) {
  const el = document.getElementById(id);
  el.focus();
  el.select();
  try {
    document.execCommand('copy');
    const status = document.getElementById(statusId);
    status.textContent = "Copied ✅";
    setTimeout(() => status.textContent = "", 1500);
  } catch (e) {
    const status = document.getElementById(statusId);
    status.textContent = "Select + Ctrl+C";
    setTimeout(() => status.textContent = "", 2000);
  }
}
function copySms(){ copyTextArea('smsText', 'copyStatus'); }
function copyToList(){ copyTextArea('toText', 'copyToStatus'); }

let ticking = false;
window.addEventListener('scroll', () => {
  if (!ticking) {
    window.requestAnimationFrame(() => {
      document.documentElement.style.setProperty('--scrollY', window.scrollY + 'px');
      ticking = false;
    });
    ticking = true;
  }
}, { passive: true });
document.documentElement.style.setProperty('--scrollY', window.scrollY + 'px');

const BDAY_INDEX = window.__BDAY_INDEX__ || {};
const INIT = window.__INIT__ || {};
let viewYear = INIT.viewYear;
let viewMonth = INIT.viewMonth;
let selected = INIT.selected || null;

const monthNames = ["January","February","March","April","May","June","July","August","September","October","November","December"];
const dow = ["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];

function pad2(n){ return String(n).padStart(2,'0'); }
function keyMMDD(m,d){ return pad2(m) + "-" + pad2(d); }
function daysInMonth(y,m){ return new Date(y, m, 0).getDate(); }
function firstDow(y,m){ return new Date(y, m-1, 1).getDay(); }
function sameDate(a,b){ return a && b && a.year===b.year && a.month===b.month && a.day===b.day; }

function setTitle(){
  const el = document.getElementById("calTitle");
  el.textContent = monthNames[viewMonth-1] + " " + viewYear;
}

function renderCalendar(){
  setTitle();
  const tbody = document.getElementById("calBody");
  tbody.innerHTML = "";

  const fd = firstDow(viewYear, viewMonth);
  const dim = daysInMonth(viewYear, viewMonth);

  const today = new Date();
  const isThisMonth = (today.getFullYear()===viewYear && (today.getMonth()+1)===viewMonth);

  let dayNum = 1;
  for (let r=0; r<6; r++){
    const tr = document.createElement("tr");
    for (let c=0; c<7; c++){
      const td = document.createElement("td");
      if (r===0 && c<fd){
        td.innerHTML = "<div class='cal-day muted'></div>";
      } else if (dayNum>dim){
        td.innerHTML = "<div class='cal-day muted'></div>";
      } else {
        const btn = document.createElement("div");
        btn.className = "cal-day";
        btn.textContent = String(dayNum);

        const k = keyMMDD(viewMonth, dayNum);
        const has = Array.isArray(BDAY_INDEX[k]) && BDAY_INDEX[k].length>0;

        if (has){
          btn.classList.add("has-bday");
          const dot = document.createElement("div");
          dot.className = "cal-dot";
          btn.appendChild(dot);
          btn.title = "Birthdays: " + BDAY_INDEX[k].join(", ");
        }

        if (isThisMonth && dayNum===today.getDate()){
          btn.classList.add("today");
        }

        const candidate = {year:viewYear, month:viewMonth, day:dayNum};
        if (sameDate(candidate, selected)){
          btn.classList.add("selected");
        }

        btn.addEventListener("click", () => {
          selected = candidate;
          updateSelectedUI();
          renderCalendar();
        });

        td.appendChild(btn);
        dayNum++;
      }
      tr.appendChild(td);
    }
    tbody.appendChild(tr);
    if (dayNum>dim) break;
  }
}

function updateSelectedUI(){
  const label = document.getElementById("calSelectedLabel");
  const genBtn = document.getElementById("calGenerateBtn");
  const genHint = document.getElementById("calGenerateHint");

  if (!selected){
    label.textContent = "Pick a day to generate the fun facts.";
    genBtn.disabled = true;
    genHint.textContent = "";
    return;
  }
  const mm = pad2(selected.month);
  const dd = pad2(selected.day);
  const pretty = monthNames[selected.month-1] + " " + dd;
  label.textContent = "Selected: " + pretty + " (click Generate)";
  genBtn.disabled = false;

  const k = mm + "-" + dd;
  if (BDAY_INDEX[k] && BDAY_INDEX[k].length){
    genHint.textContent = "🎂 Birthdays: " + BDAY_INDEX[k].join(", ");
  } else {
    genHint.textContent = "";
  }
}

function goMonth(delta){
  let m = viewMonth + delta;
  let y = viewYear;
  if (m<1){ m=12; y--; }
  if (m>12){ m=1; y++; }
  viewMonth = m;
  viewYear = y;

  if (!selected){
    selected = {year:viewYear, month:viewMonth, day:1};
  } else {
    if (selected.year===viewYear && selected.month===viewMonth){
      const dim = daysInMonth(viewYear, viewMonth);
      if (selected.day>dim) selected.day = dim;
    }
  }

  updateSelectedUI();
  renderCalendar();
}

function generate(){
  if (!selected) return;
  const mm = pad2(selected.month);
  const dd = pad2(selected.day);
  window.location.href = "/?date=" + mm + "-" + dd + "&show=1";
}

document.addEventListener("DOMContentLoaded", () => {
  const head = document.getElementById("calHeadRow");
  head.innerHTML = "";
  for (const d of dow){
    const th = document.createElement("th");
    th.textContent = d;
    head.appendChild(th);
  }

  document.getElementById("calPrev").addEventListener("click", () => goMonth(-1));
  document.getElementById("calNext").addEventListener("click", () => goMonth(1));
  document.getElementById("calGenerateBtn").addEventListener("click", generate);

  if (!selected){
    const t = new Date();
    selected = {year:viewYear, month:viewMonth, day: t.getDate()};
  }

  updateSelectedUI();
  renderCalendar();
});
"""
