#!/usr/bin/env python3
"""Profile picture and covers for the social accounts (Bluesky, Facebook), in the grammar of the share card
(tools/nd_brand_og.py): nero ground, stripe sleeve, Anton wordmark, Fragment Mono small print. Added Nov 14, 2026.
  python3 tools/nd_social_brand.py [--out assets/brand] [--fonts build/fonts]
Writes avatar-nd-1000.png (the ND mark the TikTok and YouTube channels use, redrawn large), bluesky-banner-1500x500.png
and facebook-cover-1640x624.png. Since Nov 15, 2026 both covers follow the YouTube channel banner's design (yt_cover)."""
import argparse, os
from PIL import Image, ImageDraw
from nd_brand_og import font, NERO, NAVY, BLUE, WHITE, SKY, GREY

RHYTHM = [17, 11, 23, 11, 17, 11, 23, 15]

def sleeve(d, x, H, scale=1.0):
    for i, w in enumerate(RHYTHM):
        w = round(w * scale); d.rectangle([x, 0, x + w, H], fill=NAVY if i % 2 == 0 else BLUE); x += w
    return x

def save(im, path, colors=24):
    im.quantize(colors=colors, method=Image.Quantize.MEDIANCUT).save(path, 'PNG', optimize=True); print(path, os.path.getsize(path), 'bytes')

def avatar(out, fonts):
    S = 1000; im = Image.new('RGB', (S, S), NERO); d = ImageDraw.Draw(im)
    f = font(fonts, 'Anton-Regular.ttf', 560)
    wn = d.textlength('N', font=f); wd = d.textlength('D', font=f); gap = 14
    x0 = (S - (wn + gap + wd)) / 2; top = d.textbbox((0, 0), 'ND', font=f)[1]; y = 150 - top
    d.text((x0, y), 'N', font=f, fill=WHITE); d.text((x0 + wn + gap, y), 'D', font=f, fill=BLUE)
    # the stripe rhythm as a row of blocks under the letters, kept inside the circle a round crop leaves
    widths = [70, 70, 70, 100]; g = 100; total = sum(widths) + g * 3; x = (S - total) / 2; yb = 800
    for w in widths:
        d.rectangle([x, yb, x + w, yb + 70], fill=BLUE); x += w + g
    save(im, os.path.join(out, 'avatar-nd-1000.png'), 16)

def wordmark(d, x, y, f):
    d.text((x, y), 'NERAZZURRI', font=f, fill=WHITE)
    d.text((x + d.textlength('NERAZZURRI ', font=f), y), 'DAILY', font=f, fill=SKY)
    return d.textlength('NERAZZURRI DAILY', font=f)

RUST_BAND, RUST_INK, RUST_RAIL = (251, 234, 231), (140, 64, 52), (231, 180, 174)

def yt_cover(W, H, fonts, k, top, inset):
    """The YouTube channel banner's design (owner's choice, Nov 15, 2026: the covers match YouTube): four thin stripes on
    each side, then centered: the mono kicker, the wordmark, the mono promise line and the CONFIRMED / REPORTED chips.
    k scales the type; top is where the stack starts; inset is how far the stripes sit from the edges."""
    im = Image.new('RGB', (W, H), NERO); d = ImageDraw.Draw(im)
    sw, sg = round(13 * k), round(15 * k)
    for side in (0, 1):
        for i in range(4):
            x = inset + i * (sw + sg) if side == 0 else W - inset - sw - i * (sw + sg)
            d.rectangle([x, 0, x + sw, H], fill=BLUE)
    mono = font(fonts, 'FragmentMono-Regular.ttf', round(24 * k)); big = font(fonts, 'Anton-Regular.ttf', round(132 * k)); chip = font(fonts, 'FragmentMono-Regular.ttf', round(20 * k))
    def center(text, y, f, fill, spacing=0):
        if spacing:
            w = sum(d.textlength(c, font=f) for c in text) + spacing * (len(text) - 1); x = (W - w) / 2
            for c in text:
                d.text((x, y), c, font=f, fill=fill); x += d.textlength(c, font=f) + spacing
        else:
            d.text(((W - d.textlength(text, font=f)) / 2, y), text, font=f, fill=fill)
    sp = round(4 * k)
    center('INTER MILAN · IN ENGLISH · EVERY MORNING', top, mono, GREY, sp)
    wm = d.textlength('NERAZZURRI DAILY', font=big); wordmark(d, (W - wm) / 2, top + round(34 * k), big)
    y2 = top + round(34 * k) + round(190 * k)
    center('THE ITALIAN PRESS, READ FOR YOU IN 90 SECONDS', y2, mono, GREY, sp)
    # chips
    ph, pv, gap = round(22 * k), round(11 * k), round(14 * k)
    def cw(t): return sum(d.textlength(c, font=chip) for c in t) + sp * (len(t) - 1) + 2 * ph
    w1, w2 = cw('CONFIRMED'), cw('REPORTED'); ch = round(20 * k) + 2 * pv + round(4 * k)
    x = (W - (w1 + gap + w2)) / 2; y = y2 + round(58 * k)
    for t, w, bg, ink, rail in (('CONFIRMED', w1, BLUE, WHITE, None), ('REPORTED', w2, RUST_BAND, RUST_INK, RUST_RAIL)):
        d.rectangle([x, y, x + w, y + ch], fill=bg, outline=rail, width=round(2 * k) if rail else 0)
        tx = x + ph
        for c in t:
            d.text((tx, y + pv), c, font=chip, fill=ink); tx += d.textlength(c, font=chip) + sp
        x += w + gap
    return im

def bluesky(out, fonts):
    """1500x500. Bluesky lays the round profile picture over the bottom left; the centered stack stays clear of it."""
    save(yt_cover(1500, 500, fonts, 1.0, 62, 150), os.path.join(out, 'bluesky-banner-1500x500.png'), 32)

def facebook(out, fonts):
    """1640x624. A phone shows only the middle 1,100 or so pixels and the page lays the profile picture over the bottom
    left, so the stack is centered, kept above the bottom band, and the stripes sit inside the phone crop."""
    save(yt_cover(1640, 624, fonts, 0.95, 120, 272), os.path.join(out, 'facebook-cover-1640x624.png'), 32)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--out', default='assets/brand'); ap.add_argument('--fonts', default='build/fonts')
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    avatar(a.out, a.fonts); bluesky(a.out, a.fonts); facebook(a.out, a.fonts)
