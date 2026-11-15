#!/usr/bin/env python3
"""nd_growth_captions.py - the Facebook and Bluesky words for the day's video, made from the
files the 6:45 social pack already wrote. Nothing is invented here: every sentence comes from
data/tiktok-ed<N>.json, plus a few fixed lines that never change.

Why a tool and not an agent: the TikTok and YouTube words are checked by the 6:45 pack. The
Facebook and Bluesky posts carry the same video, so they say the same thing, cut to fit. An
agent rewriting them each morning could add a fact; this cannot.

  python3 tools/nd_growth_captions.py 75        prints JSON:
  {"n", "date", "video", "facebook": {"title", "caption", "comment"},
   "bluesky": {"text", "alt"}}
  It exits with an error, and prints nothing usable, when the day's caption cannot be cleaned
  with certainty; the caller then posts the plain link post instead.

Facebook (owner's decision, Nov 15, 2026: the video goes to Facebook as its own post): the
caption has NO link - Facebook shows link posts to fewer people and asks pages to put the
link in a comment - so the link is the first comment, and the caption's first line says so
(seen live on Nov 15, 2026: a Reel's caption is folded after about two lines).
Bluesky: one post = the video + a tappable link + hashtags, 300 characters at most. Hashtags
are how Bluesky's topic feeds and tag searches find a post, so every Bluesky post of ours ends
with the day's tags: three when they fit, else two (owner's decision, Nov 15, 2026).

  python3 tools/nd_growth_captions.py --ft 2026-11-22     the same for the FULL-TIME card of that
  match date, made from data/tiktok-ft-<date>.json: {"n", "date", "video", "facebook", "bluesky"}.
  Its links land on /subscribe/ (the match is in tomorrow morning's edition, not today's).
  python3 tools/nd_growth_captions.py --debate 2026-11-18  the same for THE DEBATE short posted on
  that date (owner's decision, Nov 15, 2026: the debate goes to Facebook and Bluesky too), made from
  data/tiktok-debate-<date>-<slug>.json: {"k", "n", "date", "video", "status", "facebook", "bluesky"}.
  "k" is the debate's number, "n" the edition of that date, "status" the build record to check.
  A debate belongs to no edition, so its links land on /subscribe/ (doors v=debate<k>).
  python3 tools/nd_growth_captions.py --question 75       the Bluesky text of the day's question:
  {"n", "question", "bluesky": {"text"}} - the question the YouTube Short asks, copied from
  data/youtube-ed<N>.json, the edition link and the day's tags.
"""
import json, re, sys

SITE = "https://www.nerazzurridaily.com"
URL_RE = re.compile(r"https?://\S+")
TAG_RE = re.compile(r"(?<![\w&/])#[^\W\d_]\w*")
FB_TOP = "Full edition, free: link in the comments."
FB_ASK = "Follow for tomorrow's edition. Free by email every morning."
FB_COMMENT = "Today's full edition, free: {link}"
BSKY_LINE = "Free every morning, in English: {link}"
FT_FB_TOP = "The morning after, in English, free by email: link in the comments."
FT_FB_ASK = "Follow for every Inter full-time card."
FT_FB_COMMENT = "Inter Milan in English, free by email every morning: {link}"
FT_BSKY_LINE = "The morning after, in English, free by email: {link}"
DB_FB_TOP = "Name your pick in the comments. The free daily email is linked there too."
DB_FB_ASK = "Follow for a new Inter debate every week."
DB_FB_COMMENT = "Inter Milan in English, free by email every morning: {link}"
DB_BSKY_ASK = "Reply with your pick."
DB_BSKY_LINE = "Inter in English, free by email every morning: {link}"
Q_BSKY_LINE = "Today's edition: {link}"
DEFAULT_TAGS = ["#Inter", "#SerieA"]

def fit(blocks_by_preference, must):
    """The first of the candidate texts that fits Bluesky's 300 characters."""
    for lines in blocks_by_preference:
        text = "\n".join(l for l in lines if l)
        if len(text) <= 300: break
    assert len(text) <= 300 and must in text
    return text

def first_sentence(text):
    """The first sentence, never cut after an abbreviation such as 'No.' and never shorter than 25 characters."""
    out = ""
    for part in re.split(r"(?<=[.!?])\s+", text.strip()):
        out = (out + " " + part).strip()
        if len(out) >= 25 and not re.search(r"\b(No|vs|St|Mr|Dr)\.$", out): break
    return out

def split_caption(caption):
    """The TikTok caption without its link, the words that introduce the link, and its hashtags.
    The 6:45 pack does not always lay these out the same way (own lines, or inline), so nothing
    here depends on the layout. Returns (the words, [hashtags in their order])."""
    tags = TAG_RE.findall(caption)
    text = TAG_RE.sub("", caption)
    while True:
        m = URL_RE.search(text)
        if not m: break
        before = text[:m.start()]
        ends = [x.end() for x in re.finditer(r"[.!?](?=\s)|\n", before)]     # where the last full sentence or line ended
        cut = ends[-1] if ends else 0
        if before[cut:].rstrip().endswith(":"): before = before[:cut]         # "Free daily digest in English:"
        text = before + " " + text[m.end():]
    text = re.sub(r"\s+", " ", text).strip()
    assert text and not URL_RE.search(text) and "#" not in text, "could not clean the caption"
    assert text[-1] in ".!?\"'”’)", "the caption does not end on a full sentence"
    return text, tags

def build(n, root="."):
    tt = json.load(open(f"{root}/data/tiktok-ed{n}.json"))
    assert tt["n"] == n, "tiktok file is for another edition"
    title = tt["title"].strip()
    hook, tags = split_caption(tt["caption"])

    fb_link = f"{SITE}/go/fb/?ed={n}&v=reel&to=/p/edition-{n}/"
    head = title if title[-1] in ".!?" else title + "."
    # Facebook folds a Reel's caption after about two lines: the title and where the link is come first.
    fb_caption = "\n\n".join([head + " " + FB_TOP, hook, FB_ASK] + ([" ".join(tags)] if tags else []))
    assert not URL_RE.search(fb_caption)

    bs_link = f"{SITE}/go/bsky/?ed={n}&v=video&to=/p/edition-{n}/"
    link_line = BSKY_LINE.format(link=bs_link)
    tag3, tag_line = " ".join(tags[:3]), " ".join(tags[:2])
    lead = first_sentence(hook)
    words = lambda x: {w for w in re.findall(r"\w+", x.lower()) if len(w) > 3}
    if len(words(lead) & words(title)) >= 0.5 * max(1, min(len(words(lead)), len(words(title)))): lead = ""   # do not say the title twice
    text = fit(([head, lead, link_line, tag3], [head, lead, link_line, tag_line], [head, link_line, tag3],
                [head, link_line, tag_line], [head, link_line], [link_line]), bs_link)

    return {"n": n, "date": tt["date"], "video": tt.get("mp4") or f"assets/video/ed{n}.mp4",
            "facebook": {"title": title, "caption": fb_caption, "comment": FB_COMMENT.format(link=fb_link)},
            "bluesky": {"text": text, "alt": f"Nerazzurri Daily, edition No. {n}, a short video with voiceover: {title}"}}

def build_ft(date, root="."):
    """The full-time card of the match played on <date> (YYYY-MM-DD), for Facebook and Bluesky."""
    assert re.match(r"^\d{4}-\d{2}-\d{2}$", date), "the date is YYYY-MM-DD"
    tt = json.load(open(f"{root}/data/tiktok-ft-{date}.json"))
    assert tt["date"] == date, "tiktok file is for another match date"
    n = int(tt["n"]); title = tt["title"].strip()
    assert tt["mp4"] == f"assets/video/ft-{date}.mp4", "unexpected video path"
    hook, tags = split_caption(tt["caption"])
    head = title if title[-1] in ".!?" else title + "."

    fb_link = f"{SITE}/go/fb/?ed={n}&v=ft&to=/subscribe/"
    fb_caption = "\n\n".join([head + " " + FT_FB_TOP, hook, FT_FB_ASK] + ([" ".join(tags)] if tags else []))
    assert not URL_RE.search(fb_caption)

    bs_link = f"{SITE}/go/bsky/?ed={n}&v=ft&to=/subscribe/"
    link_line = FT_BSKY_LINE.format(link=bs_link)
    text = fit(([head, link_line, " ".join(tags[:3])], [head, link_line, " ".join(tags[:2])], [head, link_line], [link_line]), bs_link)
    return {"n": n, "date": date, "video": tt["mp4"],
            "facebook": {"title": title, "caption": fb_caption, "comment": FT_FB_COMMENT.format(link=fb_link)},
            "bluesky": {"text": text, "alt": f"Nerazzurri Daily full-time card, a short video with voiceover: {title}"}}

def build_debate(date, root="."):
    """THE DEBATE short posted on <date> (YYYY-MM-DD), for Facebook and Bluesky."""
    import glob
    assert re.match(r"^\d{4}-\d{2}-\d{2}$", date), "the date is YYYY-MM-DD"
    files = sorted(glob.glob(f"{root}/data/tiktok-debate-{date}-*.json"))
    assert len(files) == 1, "there is not exactly one debate for that date"
    tt = json.load(open(files[0]))
    assert tt["date"] == date, "tiktok file is for another date"
    k = int(tt["n"]); slug = tt["slug"]; title = tt["title"].strip()
    assert re.match(r"^[a-z0-9-]+$", slug) and tt["mp4"] == f"assets/video/debate-{date}-{slug}.mp4", "unexpected video path"
    n = None                                                 # the edition of that date: Bluesky requests are named after it
    for f in glob.glob(f"{root}/data/edition-*.json"):
        e = json.load(open(f))
        if e.get("date") == date: n = int(e["n"])
    assert n, "no edition is dated that day"
    hook, tags = split_caption(tt["caption"])
    assert f"debate{k}" in tt["caption"], "the caption's door is not this debate's"
    head = title if title[-1] in ".!?" else title + "."

    fb_link = f"{SITE}/go/fb/?v=debate{k}&to=/subscribe/"
    fb_caption = "\n\n".join([head + " " + DB_FB_TOP, hook, DB_FB_ASK] + ([" ".join(tags)] if tags else []))
    assert not URL_RE.search(fb_caption)

    bs_link = f"{SITE}/go/bsky/?v=debate{k}&to=/subscribe/"
    link_line = DB_BSKY_LINE.format(link=bs_link)
    text = fit(([head, DB_BSKY_ASK, link_line, " ".join(tags[:3])], [head, DB_BSKY_ASK, link_line, " ".join(tags[:2])],
                [head, DB_BSKY_ASK, link_line], [head, link_line], [link_line]), bs_link)
    return {"k": k, "n": n, "date": date, "video": tt["mp4"], "status": f"review/social-debate-{date}-{slug}/status.json",
            "facebook": {"title": title, "caption": fb_caption, "comment": DB_FB_COMMENT.format(link=fb_link)},
            "bluesky": {"text": text, "alt": f"Nerazzurri Daily, THE DEBATE No. {k}, a short video with voiceover: {title}"}}

def build_question(n, root="."):
    """The day's question for Bluesky: the one the YouTube Short asks, the edition link, the day's tags."""
    yt = json.load(open(f"{root}/data/youtube-ed{n}.json"))
    assert yt["n"] == n, "youtube file is for another edition"
    q = re.sub(r"\s+", " ", URL_RE.sub("", yt["comment"])).strip()
    q = re.split(r"\s*Reply in the comments\b", q)[0].strip()
    # a question, or a question followed by a short prompt such as "Name one." or "One word."
    assert "?" in q and len(q.rsplit("?", 1)[1]) <= 20 and q[-1] in "?." and "#" not in q and 15 <= len(q) <= 200, "no clean question in the comment"
    try: tags = split_caption(json.load(open(f"{root}/data/tiktok-ed{n}.json"))["caption"])[1]
    except Exception: tags = []
    tags = tags or DEFAULT_TAGS
    link = f"{SITE}/go/bsky/?ed={n}&v=q&to=/p/edition-{n}/"
    link_line = Q_BSKY_LINE.format(link=link)
    text = fit(([q, link_line, " ".join(tags[:3])], [q, link_line, " ".join(tags[:2])], [q, link_line], [q]), q)
    return {"n": n, "date": yt["date"], "question": q, "bluesky": {"text": text}}

if __name__ == "__main__":
    if sys.argv[1] == "--ft": out = build_ft(sys.argv[2])
    elif sys.argv[1] == "--debate": out = build_debate(sys.argv[2])
    elif sys.argv[1] == "--question": out = build_question(int(sys.argv[2]))
    else: out = build(int(sys.argv[1]))
    print(json.dumps(out, indent=1, ensure_ascii=False))
