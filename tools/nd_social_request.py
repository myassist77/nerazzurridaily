#!/usr/bin/env python3
"""Nerazzurri Daily — write and validate a SOCIAL REQUEST, the one text file the social workflow builds from.

Since Oct 21, 2026 the social runs do not render in the Composio sandbox (it lost outbound network and the
github proxy). They render locally for the owner's chat copy, then commit data/social/<job>.json — written
by this tool — with the GITHUB_COMMIT_MULTIPLE_FILES tool. .github/workflows/social.yml voices, renders,
mixes, QCs and commits the post files, and leaves review/social-<job>/status.json for the run to read.

    python3 tools/nd_social_request.py --job ed49 --kind daily --n 49 --date 2026-10-21 --slug keeper-call \\
        --beats beats.voiced.json --tiktok tiktok.json --youtube youtube.json \\
        [--captions captions.txt] [--manifest manifest.json] [--index-row index.json] [--force] --out data/social/ed49.json

Daily defaults (kind=daily): name ND-{date}-ed{n}-{slug}; outputs assets/video/ed{n}.mp4, ed{n}-thumb.png (16:9),
ed{n}-thumb-9x16.png; qc assets/qc/latest-contact.jpg + latest-thumb-9x16.png + latest-thumb-16x9.png;
post files data/tiktok-ed{n}.json and data/youtube-ed{n}.json. Debate (kind=debate, --name required):
outputs assets/video/{name}.mp4, {name}-thumb.png, {name}-thumb-9x16.png; qc assets/qc/debate-contact.jpg;
post files data/tiktok-{name}.json and data/youtube-{name}.json when given.
The tiktok / youtube JSON files are the post files EXACTLY as the task prompt specifies them, except that
"seconds", "beats" and "created_at_utc" may be null — the workflow fills those from the file it built.
Validation here is the same the workflow applies, so a request that passes here will not fail there on shape.
"""
import argparse, json, os, re, sys

AP = argparse.ArgumentParser()
AP.add_argument("--job", required=True); AP.add_argument("--kind", choices=["daily", "debate", "weekly"], required=True)
AP.add_argument("--n", type=int); AP.add_argument("--date"); AP.add_argument("--slug"); AP.add_argument("--name")
AP.add_argument("--beats"); AP.add_argument("--tiktok"); AP.add_argument("--youtube")
AP.add_argument("--captions"); AP.add_argument("--manifest"); AP.add_argument("--index-row"); AP.add_argument("--weekly-end", type=int)
AP.add_argument("--force", action="store_true"); AP.add_argument("--out", required=True)
A = AP.parse_args()

def die(m): sys.exit(f"REQUEST FAILED: {m}")
def load(p):
    try: return json.load(open(p, encoding="utf-8"))
    except Exception as e: die(f"{p}: {e}")

TT_KEYS = ["n", "date", "slug", "mp4", "title", "caption", "seconds", "created_at_utc"]
YT_KEYS = ["n", "date", "slug", "mp4", "thumb", "title", "description", "tags", "comment", "seconds", "beats", "created_at_utc"]
if not re.match(r"^[A-Za-z0-9._-]+$", A.job): die("--job is a file basename")

r = {"job": A.job, "kind": A.kind}
if A.kind == "daily":
    if not (A.n and A.date and A.slug): die("daily needs --n --date --slug")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", A.date): die("--date is YYYY-MM-DD")
    if not re.match(r"^[a-z0-9]+(-[a-z0-9]+){1,3}$", A.slug): die("--slug is two to four lowercase hyphenated words")
    r["name"] = A.name or f"ND-{A.date}-ed{A.n}-{A.slug}"
    r["outputs"] = {"mp4": f"assets/video/ed{A.n}.mp4", "thumb16": f"assets/video/ed{A.n}-thumb.png", "thumb9": f"assets/video/ed{A.n}-thumb-9x16.png"}
    r["qc"] = {"contact": "assets/qc/latest-contact.jpg", "thumb9": "assets/qc/latest-thumb-9x16.png", "thumb16": "assets/qc/latest-thumb-16x9.png"}
    if A.job != f"ed{A.n}": die(f"daily job is ed{A.n}, not {A.job}")
elif A.kind == "debate":
    if not A.name: die("debate needs --name (e.g. debate-2026-10-21-greatest-keeper)")
    r["name"] = A.name
    r["outputs"] = {"mp4": f"assets/video/{A.name}.mp4", "thumb16": f"assets/video/{A.name}-thumb.png", "thumb9": f"assets/video/{A.name}-thumb-9x16.png"}
    r["qc"] = {"contact": "assets/qc/debate-contact.jpg"}
else:
    if not A.weekly_end: die("weekly needs --weekly-end N")
    r["name"] = A.name or f"weekly-ed{A.weekly_end}"; r["weekly"] = {"end": A.weekly_end}
    r["outputs"] = {"mp4": f"assets/video/weekly-ed{A.weekly_end}.mp4", "thumb16": f"assets/video/weekly-ed{A.weekly_end}-thumb.png", "post": f"data/youtube-weekly-ed{A.weekly_end}.json"}
    r["qc"] = {}
if not re.match(r"^[A-Za-z0-9._-]+$", r["name"]): die("name is a file basename")

if A.kind != "weekly":
    if not A.beats: die("--beats is required")
    b = load(A.beats)
    beats = b.get("beats")
    if not isinstance(beats, list) or not beats: die("beats JSON has no beats")
    ids = [x.get("id") for x in beats]
    if len(set(ids)) != len(ids) or not all(ids): die("every beat needs a unique id")
    for x in beats:
        vo = x.get("vo")
        if not isinstance(vo, str) or not vo.strip(): die(f"beat {x.get('id')}: no vo line")
        if re.search(r"\d", vo): die(f"beat {x.get('id')}: a digit in the vo line — write numbers as words")
        if not isinstance(x.get("duration"), (int, float)) or x["duration"] <= 0: die(f"beat {x.get('id')}: duration")
    if A.kind == "daily" and not b.get("sunday_scorecard") and len(beats) != 6: die(f"a daily video has exactly six beats, this has {len(beats)}")
    if A.kind == "daily" and len(beats) > 7: die("at most seven beats with the voice")
    if A.kind == "daily" and (b.get("thumbnail") or {}).get("style") not in ("number", "split"): die('thumbnail.style must be "number" (or "split" on a day with no figure)')
    if b.get("voice"):
        total = sum(x["duration"] for x in beats)
        if not 20.0 <= total <= 39.0: die(f"voiced beats sum to {total:.2f}s, outside 20–39 s")
    r["beats"] = b
    r["post_files"] = {}
    tt_path = f"data/tiktok-{A.job}.json" if A.kind == "daily" else f"data/tiktok-{r['name']}.json"
    yt_path = f"data/youtube-{A.job}.json" if A.kind == "daily" else f"data/youtube-{r['name']}.json"
    if A.tiktok:
        t = load(A.tiktok)
        if list(t.keys()) != TT_KEYS: die(f"tiktok keys are {list(t.keys())}, must be exactly {TT_KEYS}")
        if A.kind == "daily" and (t["n"] != A.n or t["date"] != A.date or t["slug"] != A.slug): die("tiktok n/date/slug differ from --n/--date/--slug")
        if t["mp4"] != r["outputs"]["mp4"]: die(f"tiktok mp4 must be {r['outputs']['mp4']}")
        if not (1 <= len(t["title"]) <= 90): die("tiktok title is 1–90 characters")
        if not (1 <= len(t["caption"]) <= 2000): die("tiktok caption is 1–2000 characters")
        if A.kind == "daily" and f"https://www.nerazzurridaily.com/go/tt/?ed={A.n}" not in t["caption"]: die("tiktok caption lacks the go/tt door link")
        r["post_files"][tt_path] = t
    if A.youtube:
        y = load(A.youtube)
        if list(y.keys()) != YT_KEYS: die(f"youtube keys are {list(y.keys())}, must be exactly {YT_KEYS}")
        if A.kind == "daily" and (y["n"] != A.n or y["date"] != A.date or y["slug"] != A.slug): die("youtube n/date/slug differ from --n/--date/--slug")
        if y["mp4"] != r["outputs"]["mp4"] or y["thumb"] != r["outputs"]["thumb9"]: die(f"youtube mp4/thumb must be {r['outputs']['mp4']} / {r['outputs']['thumb9']}")
        if not (2 <= len(y["title"]) <= 100): die("youtube title is 2–100 characters")
        if not (1 <= len(y["description"]) <= 5000): die("youtube description is 1–5000 characters")
        if A.kind == "daily" and f"https://www.nerazzurridaily.com/go/yt/?ed={A.n}" not in y["description"]: die("youtube description lacks the go/yt door link")
        if not isinstance(y["tags"], list) or any(not isinstance(s, str) or s.startswith("#") for s in y["tags"]): die("youtube tags is a list of strings without #")
        if not isinstance(y["comment"], str) or not y["comment"].strip(): die("youtube comment is the pinned-comment text")
        r["post_files"][yt_path] = y
    if A.kind == "daily" and set(r["post_files"]) != {tt_path, yt_path}: die("a daily request needs both --tiktok and --youtube")
if A.captions: r["captions"] = open(A.captions, encoding="utf-8").read()
if A.manifest: r["manifest"] = load(A.manifest)
if A.index_row: r["index_row"] = load(A.index_row)
if A.force: r["force"] = True

os.makedirs(os.path.dirname(A.out) or ".", exist_ok=True)
s = json.dumps(r, ensure_ascii=False, indent=1) + "\n"
open(A.out, "w", encoding="utf-8").write(s)
print(f"REQUEST OK {A.out} — job {r['job']} ({r['kind']}), name {r['name']}, {len(s.encode())} bytes, "
      f"{len((r.get('beats') or {}).get('beats', []))} beats, post files {list(r.get('post_files', {}).keys())}")
