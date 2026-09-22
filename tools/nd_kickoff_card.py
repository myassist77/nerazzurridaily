#!/usr/bin/env python3
"""The Kickoff Card: all 38 Inter Serie A dates of 2026-27 on one 1080x1920 phone wallpaper (PIL, no browser).
  python3 tools/nd_kickoff_card.py [--out assets/kickoff-card-2026-27.png] [--fonts build/fonts]
Reads data/season-2026-27.json. It is the signup bonus linked from the welcome email and /subscribe/confirmed/."""
import argparse, json, os, urllib.request
from PIL import Image, ImageDraw, ImageFont
NERO, PAPER, AZZ, LAZZ, LINK, PINK, FAINT, MUTED, RULE = "#06080F", "#EEF1F6", "#2B5BB8", "#4A7BE0", "#8FB2F0", "#E7B4AE", "#5A647E", "#B9C2D6", "#1A2238"
GF = "https://raw.githubusercontent.com/google/fonts/main/ofl/"
FONTS = {"anton": GF + "anton/Anton-Regular.ttf", "oswald": GF + "oswald/Oswald%5Bwght%5D.ttf",
         "mono": GF + "ibmplexmono/IBMPlexMono-Regular.ttf", "mono5": GF + "ibmplexmono/IBMPlexMono-Medium.ttf"}
BIG = {"Milan", "Juventus", "Napoli"}

def load_fonts(d):
    os.makedirs(d, exist_ok=True); out = {}
    for k, u in FONTS.items():
        p = os.path.join(d, k + ".ttf")
        if not os.path.exists(p): urllib.request.urlretrieve(u, p)
        out[k] = p
    return out

def F(path, size, wght=None):
    f = ImageFont.truetype(path, size)
    if wght is not None:
        try: f.set_variation_by_axes([wght])
        except Exception: pass
    return f

def render(out, fontdir):
    season = json.load(open("data/season-2026-27.json", encoding="utf-8"))
    FIX = [(r["md"], r["dates"], r["opponent"], "H" if r["venue"] == "HOME" else "A") for r in season["rows"]]
    assert len(FIX) == 38
    fp = load_fonts(fontdir); W, H = 1080, 1920
    im = Image.new("RGB", (W, H), NERO); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, int(W * .62), 14], fill=AZZ); d.rectangle([int(W * .62), 0, W, 14], fill=PINK)
    def text(x, y, s, font, fill, spacing=0, anchor="la"):
        if spacing == 0:
            d.text((x, y), s, font=font, fill=fill, anchor=anchor); return d.textlength(s, font=font)
        cx = x
        for ch in s:
            d.text((cx, y), ch, font=font, fill=fill, anchor=anchor); cx += d.textlength(ch, font=font) + spacing
        return cx - x
    def width(s, font, spacing=0): return sum(d.textlength(c, font=font) + spacing for c in s) - (spacing if s else 0)
    text(64, 78, "SERIE A 2026-27 \u00b7 INTER \u00b7 ALL 38", F(fp["mono5"], 26), LINK, spacing=4.7)
    h1 = F(fp["anton"], 132); w1 = text(64, 104, "THE KICKOFF ", h1, PAPER); text(64 + w1, 104, "CARD.", h1, LAZZ)
    sub = F(fp["oswald"], 30, 400)
    for i, line in enumerate(["Every Inter league date on one screen. Kickoff times land in Eastern time in your",
                              "edition once the league sets them."]):
        text(64, 270 + i * 39, line, sub, MUTED)
    f_md, f_d, f_opp, f_ha = F(fp["mono"], 22), F(fp["mono"], 22), F(fp["oswald"], 34, 500), F(fp["mono"], 18)
    top, rowh, colw, gap = 386, 64, (W - 128 - 40) // 2, 40
    for col in (0, 1):
        x0 = 64 + col * (colw + gap)
        for i, (md, dt, opp, ha) in enumerate(FIX[col * 19:(col + 1) * 19]):
            y = top + i * rowh; base = y + 44
            d.text((x0, base), f"{md:02d}", font=f_md, fill=FAINT, anchor="ls")
            d.text((x0 + 48, base), dt, font=f_d, fill=LINK, anchor="ls")
            d.text((x0 + 224, base), opp, font=f_opp, fill="#FFFFFF" if opp in BIG else PAPER, anchor="ls")
            if opp in BIG:
                ox = x0 + 224 + d.textlength(opp, font=f_opp) + 12; d.ellipse([ox, base - 17, ox + 10, base - 7], fill=PINK)
            tag = "HOME" if ha == "H" else "AWAY"; tw = width(tag, f_ha, 2.2)
            text(x0 + colw - tw, base, tag, f_ha, LAZZ if ha == "H" else FAINT, spacing=2.2, anchor="ls")
            d.line([x0, y + rowh - 1, x0 + colw, y + rowh - 1], fill=RULE, width=1)
    ly = top + 19 * rowh + 22 + 14
    d.ellipse([66, ly - 5, 76, ly + 5], fill=PINK)
    text(86, ly, "DERBY / JUVE / NAPOLI   \u00b7   HOME = SAN SIRO   \u00b7   WEEKEND DATES, EUROPE", F(fp["mono"], 19), FAINT, spacing=1.0, anchor="lm")
    fy = H - 64
    d.line([64, fy - 150, W - 64, fy - 150], fill=AZZ, width=2)
    fb, fr = F(fp["oswald"], 26, 500), F(fp["oswald"], 26, 400)
    y = fy - 150 + 26 + 4
    wb = text(64, y, "Welcome aboard.", fb, PAPER); text(64 + wb + 8, y, "Every kickoff in Eastern time, in your inbox, every", fr, MUTED)
    text(64, y + 35, "morning. Save this to your phone.", fr, MUTED)
    text(64, y + 70, "Source: " + season["source"] + ".", fr, MUTED)
    fa = F(fp["anton"], 34); d.text((W - 64, fy - 40), "NERAZZURRI DAILY", font=fa, fill=PAPER, anchor="rs")
    fm = F(fp["mono"], 20); s2 = "NERAZZURRIDAILY.COM"; w2 = width(s2, fm, 2.8)
    text(W - 64 - w2, fy - 10, s2, fm, LINK, spacing=2.8, anchor="ls")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    im.quantize(colors=48, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(out, optimize=True)
    print(out, os.path.getsize(out), "bytes")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="assets/kickoff-card-2026-27.png"); ap.add_argument("--fonts", default="build/fonts")
    a = ap.parse_args(); render(a.out, a.fonts)
