#!/usr/bin/env python3
"""Nerazzurri Daily — edition controls, v2 (Sept 14, 2026).

    python3 nd_checks.py --text edition.txt [--html render.html] [--subject "..."] [--subtitle "..."]
                         [--date "September 14"] [--site www.nerazzurridaily.com] [--json report.json]

Runs the checks the daily prompt relies on, as code. Exit 1 on any FAIL. WARNs never stop the build
but must be listed in the review email. Input --text is get_post_content(format=text); --html is the
email render (format=html). Everything is plain regex on the visible text — no network, no model.

Checks (id → what):
  brit        British spellings / hyphenated kick-off, line-up; day-first dates
  tz          EST/EDT labels; CEST or CET time without an ET time before it on the same line;
              bare 24-hour clock (e.g. "at 16:00") with no ET equivalent on the line
  falsefriend Italian-press calques and false friends (see FALSE_FRIENDS) unless glossed
  gloss       Sky Sport without "Italia"; "Ronaldo" without a disambiguator; Gazzetta/Appiano unglossed
  length      prose words between the dek and SOURCES: WARN > 500, FAIL > 800; reading time at 238 wpm
  sentences   any sentence over 30 words (FAIL over 40), average sentence length WARN > 24
  flesch      Flesch reading ease on the prose: WARN < 55, FAIL < 45 (heuristic syllables)
  dates       masthead alt, subtitle, subject and --date all name the same "Month D"; "Sept" never used
  result      LATEST RESULT block: header names a men's fixture but the body is about the women, or the
              scorers line is missing while the note promises club match reports
  poll        "RESULTS TOMORROW" promised but no YESTERDAY line in the edition
  terms       register colour words: "red bar"/"pink bar" in copy (house term is "rust bar")
  footer      "Fan-made" and "Not affiliated" present
  links       (html) any *.beehiiv.com site host → FAIL; lists external URLs to fetch; utm stripped
"""
import argparse, json, re, sys, html as H
from urllib.parse import urlparse

AP = argparse.ArgumentParser()
AP.add_argument("--text", required=True)
AP.add_argument("--html")
AP.add_argument("--subject", default="")
AP.add_argument("--subtitle", default="")
AP.add_argument("--date", default="", help='today (ET) as "Month D", e.g. "September 14"')
AP.add_argument("--site", default="www.nerazzurridaily.com")
AP.add_argument("--json")
A = AP.parse_args()

txt = open(A.text, encoding="utf-8").read()
lines = txt.splitlines()
fails, warns, info = [], [], {}
def FAIL(cid, msg): fails.append(f"{cid}: {msg}")
def WARN(cid, msg): warns.append(f"{cid}: {msg}")

# ---- prose block: between the dek (first paragraph after the masthead) and SOURCES -------------
m_src = re.search(r"\nSOURCES:", txt)
body = txt[: m_src.start()] if m_src else txt
body = re.sub(r"View image:.*?\]\n", "", body, flags=re.S)
prose_lines = [l for l in body.splitlines()
               if l.strip() and not l.startswith(("----", "View image", "Caption:", "**", "#", "_"))
               and not re.fullmatch(r"[A-Z0-9 ·'’&\-–—:,.()/+]+", l.strip())]
prose = " ".join(prose_lines)
prose = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", prose)          # markdown links → text
words = re.findall(r"[A-Za-zÀ-ÿ'’]+", prose)
n_words = len(words)
info["prose_words"] = n_words
info["read_seconds"] = round(n_words / 238 * 60)
if n_words > 800: FAIL("length", f"{n_words} prose words (limit 800)")
elif n_words > 500: WARN("length", f"{n_words} prose words (target ≤ 500)")

# ---- sentences & Flesch -------------------------------------------------------------------------
sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z“\"])", prose) if len(s.split()) > 2]
long_s = [(len(s.split()), s) for s in sents if len(s.split()) > 30]
for n, s in long_s:
    (FAIL if n > 40 else WARN)("sentences", f"{n} words: “{s[:110]}…”")
avg = (sum(len(s.split()) for s in sents) / len(sents)) if sents else 0
info["avg_sentence_words"] = round(avg, 1)
if avg > 24: WARN("sentences", f"average sentence length {avg:.1f} words (target ≤ 24)")
def syl(w):
    w = w.lower(); w = re.sub(r"e$", "", w) if len(w) > 3 else w
    return max(1, len(re.findall(r"[aeiouy]+", w)))
if sents and n_words:
    fre = 206.835 - 1.015 * (n_words / len(sents)) - 84.6 * (sum(syl(w) for w in words) / n_words)
    info["flesch_reading_ease"] = round(fre, 1)
    if fre < 45: FAIL("flesch", f"reading ease {fre:.0f} (must be ≥ 45; target ≥ 55)")
    elif fre < 55: WARN("flesch", f"reading ease {fre:.0f} (target ≥ 55)")

# ---- British forms, day-first dates -------------------------------------------------------------
BRIT = ["colour", "favourite", "defence", "centre", "organis", "realis", "programme", "travelling",
        "kick-off", "line-up", "fixture list", "sacked", "football pitch", "the ground", "full house"]
for b in BRIT:
    if re.search(r"\b" + re.escape(b), txt, re.I): FAIL("brit", f"British form “{b}”")
for d in re.findall(r"\b\d{1,2} (?:January|February|March|April|May|June|July|August|September|October|November|December)\b", txt):
    FAIL("brit", f"day-first date “{d}”")

# ---- time zones ---------------------------------------------------------------------------------
for tz in re.findall(r"\b(EST|EDT)\b", txt): FAIL("tz", f"“{tz}” label — write ET")
for l in lines:
    if re.search(r"\d{1,2}:\d{2}\s?(?:CEST|CET)\b", l) and not re.search(r"\d{1,2}(?::\d{2})?\s?(?:AM|PM)\s?ET\b", l):
        FAIL("tz", f"CEST/CET time without an ET time before it: “{l.strip()[:90]}”")
    for t in re.findall(r"\b(\d{1,2}:\d{2})(?!\s?(?:AM|PM|ET|CEST|CET|'))\b", l):
        if not re.search(r"\b(?:AM|PM)\s?ET\b", l):
            FAIL("tz", f"bare clock “{t}” with no ET equivalent: “{l.strip()[:90]}”")

# ---- false friends / calques --------------------------------------------------------------------
FALSE_FRIENDS = {
    r"\bcommuniqu[ée]\b": "the club's statement / announcement",
    r"\bthe mister\b": "the coach / manager",
    r"\bbomber\b": "striker",
    r"\btifosi\b": "fans (or gloss it)",
    r"\b(?:calcio)?mercato\b": "the transfer window (gloss on first use)",
    r"\bprobable (?:formation|XI|lineup)\b": "projected lineup",
    r"\binfortunio\b": "injury",
    r"\brifinitura\b": "final training session",
    r"\bkeeping the gloves\b": "staying in goal",
    r"\bwrites that\b": "reports that",
    r"\bborn in (?:19|20)\d\d\b": "give the age",
    r"\bmuscle fatigue\b": "a minor muscle issue",
    r"\bthe (?:last|final) tickets\b": "a limited number of tickets remain",
    r"\b(?:at|on) \d{1,2}(?:'|’)?(?=[ ,.])(?! ?(?:AM|PM))": "in the Nth minute",
    r"\bthe (?:Pole|Turk|Argentine|Frenchman|Dutchman|German|Croatian|Austrian)\b": "use the player's name",
    r"\ban interior\b": "a midfielder",
    r"\bat the last\b": "late on",
    r"\bhe will be seen\b": "we'll see",
    r"\btechnical staff\b": "coaching staff",
    r"\bthe directive\b": "the board",
    r"\bfrom here to\b": "by",
    r"\bgiornata\b": "matchday (gloss once)",
    r"\bnet (?:a|per) season\b": "add: Italian salaries are quoted after tax",
    r"\bseason-ticket resale\b": "explain, or cut",
}
def glossed(l, m):
    tail = l[m.end(): m.end() + 40]
    return "—" in tail[:12] or tail.lstrip().startswith("(") or (l[max(0, m.start()-1):m.start()] == "_")
for pat, fix in FALSE_FRIENDS.items():
    for l in lines:
        for m in re.finditer(pat, l, re.I):
            if not glossed(l, m):
                FAIL("falsefriend", f"“{m.group(0)}” → {fix}: “{l.strip()[:90]}”")

# ---- glosses & disambiguation -------------------------------------------------------------------
if re.search(r"\bSky Sport\b(?! Italia)", txt) and not re.search(r"Sky Sport Italia", txt):
    WARN("gloss", "Sky Sport never named as Sky Sport Italia (US readers know Sky Sports UK)")
if re.search(r"\bRonaldo\b", txt) and not re.search(r"(Brazilian|the original Ronaldo|Ronaldo Nazário|ex-Inter)", txt):
    FAIL("gloss", "“Ronaldo” is not disambiguated from Cristiano")
if re.search(r"\bGazzetta\b", txt) and not re.search(r"Gazzetta[^.\n]{0,60}(sports daily|newspaper|paper)", txt):
    WARN("gloss", "Gazzetta dello Sport not glossed (Italy's largest sports daily) on first use")
if re.search(r"\bAppiano\b", txt) and not re.search(r"Appiano[^.\n]{0,60}(training|base)", txt):
    WARN("gloss", "Appiano Gentile not glossed as Inter's training ground")

# ---- dates ---------------------------------------------------------------------------------------
MON = r"(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
alt = re.search(r"\[Nerazzurri Daily Edition No\. (\d+), [A-Za-z]+, (" + MON + r" \d{1,2}), (\d{4})", txt)
info["edition_from_masthead"] = int(alt.group(1)) if alt else None
def md(s):
    m = re.search(r"(" + MON + r")\.? (\d{1,2})", s or "")
    if not m: return None
    full = {"Jan":"January","Feb":"February","Mar":"March","Apr":"April","Jun":"June","Jul":"July","Aug":"August","Sep":"September","Oct":"October","Nov":"November","Dec":"December"}
    return f"{full.get(m.group(1), m.group(1))} {int(m.group(2))}"
seen = {"masthead": md(alt.group(2)) if alt else None, "subtitle": md(A.subtitle), "subject": md(A.subject), "today": md(A.date)}
present = {k: v for k, v in seen.items() if v}
if len(set(present.values())) > 1: FAIL("dates", f"dates disagree: {present}")
info["dates"] = present
if re.search(r"\bSept\b", A.subject + " " + A.subtitle + " " + txt): FAIL("dates", "“Sept” used — the abbreviation is “Sep”")

# ---- LATEST RESULT block sanity ----------------------------------------------------------------
m = re.search(r"\*\*LATEST RESULT\*\*[^\n]*\n(.*?)(?=\n\*\*NEXT UP\*\*)", txt, re.S)
if m:
    blk = m.group(1); head = re.search(r"### (.+)", blk)
    if head and "Women" not in head.group(1) and re.search(r"\bWomen\b", blk):
        FAIL("result", f"LATEST RESULT header “{head.group(1)}” but the body is about Inter Women")
    if "club's own match reports" in blk and not re.search(r"\b\d{1,2}'", blk):
        FAIL("result", "scorers-and-minutes line missing under a men's result")

# ---- poll promise --------------------------------------------------------------------------------
if re.search(r"RESULTS TOMORROW|Results in tomorrow", txt, re.I) and not re.search(r"YESTERDAY", txt):
    FAIL("poll", "edition promises results tomorrow but carries no YESTERDAY line (write “no votes yet” if that is the case)")

# ---- house terms ---------------------------------------------------------------------------------
for bad in ["red bar", "pink bar"]:
    if re.search(r"\b" + bad + r"\b", txt, re.I): FAIL("terms", f"“{bad}” — the house term is “rust bar” (email) / matches the site")

# ---- footer --------------------------------------------------------------------------------------
src = (open(A.html, encoding="utf-8").read() if A.html else "") + txt
if not re.search(r"Fan-made", src): FAIL("footer", "“Fan-made.” missing")
if not re.search(r"Not affiliated", src): FAIL("footer", "“Not affiliated with FC Internazionale Milano.” missing")

# ---- links (html) --------------------------------------------------------------------------------
if A.html:
    hrefs = re.findall(r'href="([^"]+)"', open(A.html, encoding="utf-8").read())
    hrefs = [H.unescape(h) for h in hrefs if h.startswith("http")]
    host = lambda u: (urlparse(u).hostname or "").lower()
    bad = sorted({h for h in hrefs if host(h).endswith("beehiiv.com") and not host(h).startswith(("media.", "beehiiv-images"))
                  and "{{" not in h})
    for b in bad: FAIL("links", f"beehiiv site host still linked: {b}")
    ext = sorted({re.sub(r"[?&]utm_[^&#]+", "", h) for h in hrefs
                  if host(h) and not host(h).endswith(("beehiiv.com", "amazonaws.com")) and host(h) != A.site.lower() and "{{" not in h})
    info["external_to_fetch"] = ext
    info["site_links"] = sorted({h for h in hrefs if host(h) == A.site.lower()})

# ---- report ----------------------------------------------------------------------------------
rep = {"fails": fails, "warns": warns, "info": info}
if A.json: json.dump(rep, open(A.json, "w"), indent=2, ensure_ascii=False)
print(f"nd_checks v2 — {len(fails)} FAIL, {len(warns)} WARN · {n_words} prose words · ~{info['read_seconds']}s read"
      + (f" · Flesch {info.get('flesch_reading_ease')}" if 'flesch_reading_ease' in info else ""))
for f in fails: print("  FAIL", f)
for w in warns: print("  WARN", w)
sys.exit(1 if fails else 0)
