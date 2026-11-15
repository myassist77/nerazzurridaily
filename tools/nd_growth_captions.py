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
Bluesky: one post = the video + a tappable link + two hashtags, 300 characters at most.
"""
import json, re, sys

SITE = "https://www.nerazzurridaily.com"
URL_RE = re.compile(r"https?://\S+")
TAG_RE = re.compile(r"(?<![\w&/])#[^\W\d_]\w*")
FB_TOP = "Full edition, free: link in the comments."
FB_ASK = "Follow for tomorrow's edition. Free by email every morning."
FB_COMMENT = "Today's full edition, free: {link}"
BSKY_LINE = "Free every morning, in English: {link}"

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
    tag_line = " ".join(tags[:2])
    lead = first_sentence(hook)
    words = lambda x: {w for w in re.findall(r"\w+", x.lower()) if len(w) > 3}
    if len(words(lead) & words(title)) >= 0.5 * max(1, min(len(words(lead)), len(words(title)))): lead = ""   # do not say the title twice
    for lines in ([head, lead, link_line, tag_line], [head, link_line, tag_line], [head, link_line], [link_line]):
        text = "\n".join(l for l in lines if l)
        if len(text) <= 300: break
    assert len(text) <= 300 and bs_link in text

    return {"n": n, "date": tt["date"], "video": tt.get("mp4") or f"assets/video/ed{n}.mp4",
            "facebook": {"title": title, "caption": fb_caption, "comment": FB_COMMENT.format(link=fb_link)},
            "bluesky": {"text": text, "alt": f"Nerazzurri Daily, edition No. {n}, a short video with voiceover: {title}"}}

if __name__ == "__main__":
    print(json.dumps(build(int(sys.argv[1])), indent=1, ensure_ascii=False))
