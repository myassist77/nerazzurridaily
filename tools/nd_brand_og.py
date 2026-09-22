#!/usr/bin/env python3
"""Static 1200x630 share card for the home page and /subscribe/ (og:image / twitter:image).
  python3 tools/nd_brand_og.py [--out assets/og/nerazzurri-daily-1200x630.png] [--fonts DIR]
Same grammar as the masthead (nero ground, stripe sleeve, Anton wordmark + headline), drawn with PIL so it
needs no browser. Fonts: Anton-Regular.ttf and FragmentMono-Regular.ttf in --fonts (default: fetched from
google/fonts on GitHub into build/fonts/). Palette-quantised so the PNG stays small."""
import argparse, os, sys, urllib.request
from PIL import Image, ImageDraw, ImageFont

FONT_URLS = {
    'Anton-Regular.ttf': 'https://raw.githubusercontent.com/google/fonts/main/ofl/anton/Anton-Regular.ttf',
    'FragmentMono-Regular.ttf': 'https://raw.githubusercontent.com/google/fonts/main/ofl/fragmentmono/FragmentMono-Regular.ttf',
}
NERO, NAVY, BLUE, WHITE, SKY, GREY = (6, 8, 15), (15, 21, 38), (74, 123, 224), (255, 255, 255), (143, 178, 240), (169, 179, 201)

def font(dirp, name, size):
    p = os.path.join(dirp, name)
    if not os.path.exists(p):
        os.makedirs(dirp, exist_ok=True); urllib.request.urlretrieve(FONT_URLS[name], p)
    return ImageFont.truetype(p, size)

def build(out, fonts):
    W, H = 1200, 630
    im = Image.new('RGB', (W, H), NERO); d = ImageDraw.Draw(im)
    # stripe sleeve, right edge (same rhythm as the masthead: 9,6,12,6,9,6,12,8 scaled x1.9)
    x = W - 128
    for i, w in enumerate([17, 11, 23, 11, 17, 11, 23, 15]):
        d.rectangle([x, 0, x + w, H], fill=NAVY if i % 2 == 0 else BLUE); x += w
    mono = font(fonts, 'FragmentMono-Regular.ttf', 30)
    anton_w = font(fonts, 'Anton-Regular.ttf', 132)
    anton_h = font(fonts, 'Anton-Regular.ttf', 92)
    d.text((70, 62), 'INTER MILAN · IN ENGLISH · EVERY MORNING', font=mono, fill=GREY)
    d.text((70, 120), 'NERAZZURRI', font=anton_w, fill=WHITE)
    wpx = d.textlength('NERAZZURRI ', font=anton_w)
    d.text((70 + wpx, 120), 'DAILY', font=anton_w, fill=SKY)
    d.text((70, 300), 'CONFIRMED, KEPT APART', font=anton_h, fill=WHITE)
    d.text((70, 396), 'FROM REPORTED.', font=anton_h, fill=WHITE)
    d.text((70, 540), 'nerazzurridaily.com  ·  free  ·  6 AM Eastern', font=mono, fill=GREY)
    im = im.quantize(colors=24, method=Image.Quantize.MEDIANCUT)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    im.save(out, 'PNG', optimize=True)
    print(out, os.path.getsize(out), 'bytes')

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='assets/og/nerazzurri-daily-1200x630.png')
    ap.add_argument('--fonts', default='build/fonts')
    a = ap.parse_args(); build(a.out, a.fonts)
