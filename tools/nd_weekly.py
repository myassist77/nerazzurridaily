#!/usr/bin/env python3
"""Nerazzurri Daily — weekly long-form video ("Inter this week, in English").

Stitches the week's daily voiced Shorts (assets/video/ed{n}.mp4) into ONE 16:9 1920x1080 video:
each 9:16 Short sits in the middle, framed by brand panels that carry the newsletter address the
whole time. Why: links in Shorts descriptions/comments are not clickable (YouTube policy since
Aug 31, 2023); links in a regular video's description ARE. The description carries chapters (one
per day) and the tracking door https://www.nerazzurridaily.com/go/yt/?ed={N}&v=weekly.

Run from a checkout of the site repo:
  python3 tools/nd_weekly.py --end N [--out build/weekly] [--fonts build/fonts]
Writes: {out}/weekly-ed{N}.mp4, {out}/weekly-ed{N}-thumb.png, {out}/youtube-weekly-ed{N}.json
Needs: ffmpeg/ffprobe, Pillow. Fonts are fetched once from github.com/google/fonts.
"""
import argparse, datetime, json, os, subprocess, sys, textwrap, urllib.request
from PIL import Image, ImageDraw, ImageFont

AP = argparse.ArgumentParser()
AP.add_argument("--end", type=int, required=True, help="last edition number of the week (normally Sunday's)")
AP.add_argument("--days", type=int, default=7)
AP.add_argument("--out", default="build/weekly")
AP.add_argument("--fonts", default="build/fonts")
A = AP.parse_args()

GF = "https://raw.githubusercontent.com/google/fonts/main/ofl/"
FONTS = {"anton": GF + "anton/Anton-Regular.ttf", "mono": GF + "ibmplexmono/IBMPlexMono-Regular.ttf",
         "mono5": GF + "ibmplexmono/IBMPlexMono-Medium.ttf"}
NERO, AZZ, ACC, INK, MUTE, WHITE = "#0B1020", "#2B5BB8", "#8FB2F0", "#EEF1F6", "#5A647E", "#ffffff"
SITE = "https://www.nerazzurridaily.com"
W, H, VW = 1920, 1080, 608          # the 9:16 Short is scaled to 608x1080, centered
VX = (W - VW) // 2


def font(k, size):
    os.makedirs(A.fonts, exist_ok=True)
    p = os.path.join(A.fonts, k + ".ttf")
    if not os.path.exists(p):
        urllib.request.urlretrieve(FONTS[k], p)
    return ImageFont.truetype(p, size)


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit("ffmpeg failed: " + " ".join(cmd[:6]) + "\n" + r.stderr[-1500:])
    return r.stdout


def dur(path):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).strip())


def wrap(draw, text, f, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=f) <= width:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines


def stripes(d, x0, y0, x1, y1):
    """The brand's stripe sleeve: thin vertical nero/azzurro bands."""
    w = 14
    for i, x in enumerate(range(x0, x1, w)):
        d.rectangle([x, y0, min(x + w - 1, x1), y1], fill=AZZ if i % 2 else "#0A2A66")


def panel_bg(path, eyebrow, day, headline, n_range):
    im = Image.new("RGB", (W, H), NERO); d = ImageDraw.Draw(im)
    stripes(d, VX - 28, 0, VX - 4, H); stripes(d, VX + VW + 4, 0, VX + VW + 28, H)
    # left panel: the newsletter, always on screen
    L = 80; LW = VX - 28 - 2 * L + 20
    d.text((L, 120), "INTER THIS WEEK · IN ENGLISH", font=font("mono5", 26), fill=ACC)
    d.text((L, 170), "NERAZZURRI", font=font("anton", 92), fill=INK)
    d.text((L, 275), "DAILY", font=font("anton", 92), fill=ACC)
    y = 470
    for ln in wrap(d, "The free daily newsletter: every Inter story in the Italian press, sorted into what the club confirmed and what the papers only reported.", font("mono", 25), LW):
        d.text((L, y), ln, font=font("mono", 25), fill=INK); y += 38
    d.text((L, 820), "SUBSCRIBE FREE", font=font("mono5", 28), fill=ACC)
    d.text((L, 860), "nerazzurridaily.com", font=font("anton", 56), fill=WHITE)
    d.text((L, 960), "link in the description", font=font("mono", 24), fill=MUTE)
    # right panel: which day this is
    R = VX + VW + 28 + 70; RW = W - R - 80
    d.text((R, 120), eyebrow, font=font("mono5", 26), fill=ACC)
    d.text((R, 170), day, font=font("anton", 80), fill=INK)
    y = 320
    for ln in wrap(d, headline, font("anton", 52), RW)[:6]:
        d.text((R, y), ln, font=font("anton", 52), fill=INK); y += 70
    d.text((R, 960), n_range, font=font("mono", 24), fill=MUTE)
    im.save(path)


def card(path, big1, big2, small):
    im = Image.new("RGB", (W, H), NERO); d = ImageDraw.Draw(im)
    stripes(d, 0, 0, W, 36); stripes(d, 0, H - 36, W, H)
    for txt, y, f, c in [(small, 330, font("mono5", 34), ACC), (big1, 400, font("anton", 150), INK), (big2, 600, font("anton", 110), WHITE)]:
        d.text(((W - d.textlength(txt, font=f)) / 2, y), txt, font=f, fill=c)
    im.save(path)


def still_clip(png, seconds, out):
    run(["ffmpeg", "-y", "-loop", "1", "-t", f"{seconds}", "-i", png, "-f", "lavfi", "-t", f"{seconds}",
         "-i", "anullsrc=r=48000:cl=stereo", "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "20", "-c:a", "aac", "-b:a", "160k", "-shortest", out])


def framed_clip(bg, short, out):
    run(["ffmpeg", "-y", "-loop", "1", "-i", bg, "-i", short, "-filter_complex",
         f"[1:v]scale={VW}:{H},setsar=1[v];[0:v][v]overlay={VX}:0:shortest=1,fps=30,format=yuv420p[o]",
         "-map", "[o]", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2", out])


def main():
    os.makedirs(A.out, exist_ok=True); tmp = os.path.join(A.out, "tmp"); os.makedirs(tmp, exist_ok=True)
    eds = []
    for n in range(A.end - A.days + 1, A.end + 1):
        mp4, ej, yj = f"assets/video/ed{n}.mp4", f"data/edition-{n}.json", f"data/youtube-ed{n}.json"
        if not (os.path.exists(mp4) and os.path.exists(ej)):
            continue
        e = json.load(open(ej, encoding="utf-8"))
        hook = e["title"]
        if os.path.exists(yj):
            hook = json.load(open(yj, encoding="utf-8"))["title"].split(" | ")[0]
        eds.append({"n": n, "date": e["date"], "hook": hook, "edition_title": e["title"], "mp4": mp4})
    if len(eds) < 3:
        sys.exit(f"only {len(eds)} daily videos found for ed{A.end - A.days + 1}–{A.end}; need 3+")
    first, last = eds[0], eds[-1]
    d0, d1 = (datetime.date.fromisoformat(x["date"]) for x in (first, last))
    span = f"{d0:%b} {d0.day}–{d1.day}" if d0.month == d1.month else f"{d0:%b} {d0.day} – {d1:%b} {d1.day}"
    n_range = f"Editions No. {first['n']}–{last['n']}"
    clips, chapters, t = [], [], 0.0
    intro = os.path.join(tmp, "intro.mp4")
    card(os.path.join(tmp, "intro.png"), "INTER THIS WEEK", span.upper(), "NERAZZURRI DAILY · IN ENGLISH")
    still_clip(os.path.join(tmp, "intro.png"), 3, intro); clips.append(intro)
    chapters.append((0.0, "This week")); t += dur(intro)
    for e in eds:
        day = datetime.date.fromisoformat(e["date"])
        bg = os.path.join(tmp, f"bg{e['n']}.png"); out = os.path.join(tmp, f"seg{e['n']}.mp4")
        panel_bg(bg, f"EDITION NO. {e['n']}", f"{day:%A}".upper() + f" {day:%b} {day.day}".upper(), e["hook"], n_range)
        framed_clip(bg, e["mp4"], out); clips.append(out)
        chapters.append((t, f"{day:%a} {day:%b} {day.day} — {e['hook']}")); t += dur(out)
    outro = os.path.join(tmp, "outro.mp4")
    card(os.path.join(tmp, "outro.png"), "EVERY MORNING, FREE", "nerazzurridaily.com", "GET IT IN YOUR INBOX")
    still_clip(os.path.join(tmp, "outro.png"), 6, outro); clips.append(outro)
    chapters.append((t, "Get it every morning"))
    lst = os.path.join(tmp, "list.txt")
    open(lst, "w").write("".join(f"file '{os.path.abspath(c)}'\n" for c in clips))
    final = os.path.join(A.out, f"weekly-ed{A.end}.mp4")
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
         "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-movflags", "+faststart", final])
    # thumbnail 1280x720
    th = Image.new("RGB", (1280, 720), NERO); d = ImageDraw.Draw(th); stripes(d, 0, 0, 1280, 24)
    d.text((70, 90), f"NERAZZURRI DAILY · {span.upper()}", font=font("mono5", 30), fill=ACC)
    d.text((70, 150), "INTER", font=font("anton", 190), fill=INK)
    d.text((70, 360), "THIS WEEK", font=font("anton", 150), fill=ACC)
    d.text((70, 590), f"{len(eds)} days · in English · sourced", font=font("mono", 34), fill=INK)
    stripes(d, 900, 24, 1280, 720)
    d.rectangle([930, 250, 1250, 470], fill=NERO)
    for txt, y, f, c in [("FREE DAILY", 275, font("mono5", 30), ACC), ("NEWSLETTER", 320, font("anton", 64), INK), ("in the description", 410, font("mono", 26), INK)]:
        d.text((950, y), txt, font=f, fill=c)
    thumb = os.path.join(A.out, f"weekly-ed{A.end}-thumb.png"); th.save(thumb)

    def ts(s):
        s = int(s); return f"{s // 60}:{s % 60:02d}"
    door = f"{SITE}/go/yt/?ed={A.end}&v=weekly"
    desc = (f"Inter Milan's week in the Italian press, in English — {span}. One story a day, sorted into what the club confirmed and what the papers only reported.\n\n"
            f"Get it free in your inbox every morning: {door}\n\n"
            + "\n".join(f"{ts(s)} {c}" for s, c in chapters)
            + "\n\nRead every edition: " + SITE + "/\n"
            + "".join(f"No. {e['n']}: {SITE}/p/edition-{e['n']}/\n" for e in eds)
            + "\nFan-made — not affiliated with FC Internazionale Milano.\n\n#Inter #InterMilan #SerieA #ForzaInter")
    meta = {"n": A.end, "kind": "weekly", "span": span, "editions": [e["n"] for e in eds],
            "mp4": f"assets/video/weekly-ed{A.end}.mp4", "thumb": f"assets/video/weekly-ed{A.end}-thumb.png",
            "title": f"Inter this week in English: {span} | Nerazzurri Daily"[:100],
            "description": desc[:4900], "tags": ["Inter", "Inter Milan", "Serie A", "Inter news", "Inter Milan news in English", "Nerazzurri"],
            "seconds": round(dur(final), 2), "door": door, "chapters": [[round(s, 2), c] for s, c in chapters]}
    json.dump(meta, open(os.path.join(A.out, f"youtube-weekly-ed{A.end}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps({k: meta[k] for k in ("title", "seconds", "editions", "door")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
