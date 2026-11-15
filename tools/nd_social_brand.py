#!/usr/bin/env python3
"""Profile picture and covers for the social accounts (Bluesky, Facebook), in the grammar of the share card
(tools/nd_brand_og.py): nero ground, stripe sleeve, Anton wordmark, Fragment Mono small print. Added Nov 14, 2026.
  python3 tools/nd_social_brand.py [--out assets/brand] [--fonts build/fonts]
Writes avatar-nd-1000.png (the ND mark the TikTok and YouTube channels use, redrawn large), bluesky-banner-1500x500.png
and facebook-cover-1640x624.png. Each cover keeps its words clear of where that platform lays the profile picture
and inside the part a phone shows."""
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

def bluesky(out, fonts):
    """1500x500. Bluesky lays the round profile picture over the bottom left, so the words sit to the right of it."""
    W, H = 1500, 500; im = Image.new('RGB', (W, H), NERO); d = ImageDraw.Draw(im)
    sleeve(d, W - 150, H, 1.2)
    mono = font(fonts, 'FragmentMono-Regular.ttf', 28); big = font(fonts, 'Anton-Regular.ttf', 128); mid = font(fonts, 'Anton-Regular.ttf', 56)
    x = 400
    d.text((x, 70), 'INTER MILAN · IN ENGLISH · EVERY MORNING', font=mono, fill=GREY)
    wordmark(d, x, 112, big)
    d.text((x, 290), 'CONFIRMED, KEPT APART FROM REPORTED.', font=mid, fill=WHITE)
    d.text((x, 400), 'nerazzurridaily.com  ·  free  ·  6 AM Eastern', font=mono, fill=GREY)
    save(im, os.path.join(out, 'bluesky-banner-1500x500.png'))

def facebook(out, fonts):
    """1640x624. A phone shows only the middle 1,100 or so pixels, and the desktop page lays the profile picture over
    the bottom left, so the words are centered and kept above the bottom band."""
    W, H = 1640, 624; im = Image.new('RGB', (W, H), NERO); d = ImageDraw.Draw(im)
    sleeve(d, W - 128, H); sleeve(d, 0, H)
    mono = font(fonts, 'FragmentMono-Regular.ttf', 28); big = font(fonts, 'Anton-Regular.ttf', 150); mid = font(fonts, 'Anton-Regular.ttf', 66)
    def center(text, y, f, fill):
        d.text(((W - d.textlength(text, font=f)) / 2, y), text, font=f, fill=fill)
    center('INTER MILAN · IN ENGLISH · EVERY MORNING', 96, mono, GREY)
    wm = d.textlength('NERAZZURRI DAILY', font=big); wordmark(d, (W - wm) / 2, 140, big)
    center('CONFIRMED, KEPT APART FROM REPORTED.', 350, mid, WHITE)
    center('nerazzurridaily.com  ·  free  ·  6 AM Eastern', 462, mono, GREY)
    save(im, os.path.join(out, 'facebook-cover-1640x624.png'))

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--out', default='assets/brand'); ap.add_argument('--fonts', default='build/fonts')
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    avatar(a.out, a.fonts); bluesky(a.out, a.fonts); facebook(a.out, a.fonts)
