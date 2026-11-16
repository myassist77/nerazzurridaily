#!/usr/bin/env python3
"""The header image of the two signup emails (confirm + welcome): the site masthead's block - eyebrow, Anton wordmark,
kit stripes - as one small PNG, because an email cannot load the wordmark face. 1288x232 (shown at 644 wide).
  python3 tools/nd_email_header.py <fonts dir>   -> assets/brand/email-header-1288x232.png
<fonts dir> holds Anton-Regular.ttf and IBMPlexMono-Medium.ttf (github.com/google/fonts, ofl/)."""
import os, sys
from PIL import Image, ImageDraw, ImageFont
W, H = 1288, 232
NERO, WHITE, SKY, GREY, S1, S2 = '#06080F', '#FFFFFF', '#8FB2F0', '#A9B3C9', '#0F1526', '#4A7BE0'
def build(fonts, out='assets/brand/email-header-1288x232.png'):
    im = Image.new('RGB', (W, H), NERO); d = ImageDraw.Draw(im)
    x = W - 136                                   # the sleeve: the site header's 68px stripe block, doubled
    for w, c in ((24, S1), (18, S2), (24, S1), (18, S2), (24, S1), (18, S2), (10, S1)):
        d.rectangle([x, 0, x + w - 1, H], fill=c); x += w
    eye = ImageFont.truetype(os.path.join(fonts, 'IBMPlexMono-Medium.ttf'), 26)
    big = ImageFont.truetype(os.path.join(fonts, 'Anton-Regular.ttf'), 104)
    tx = 56; t = 'INTER MILAN · IN ENGLISH · EVERY MORNING'
    for ch in t:                                  # letter-spaced eyebrow, as on the site
        d.text((tx, 44), ch, font=eye, fill=GREY); tx += d.textlength(ch, font=eye) + 3.6
    d.text((56, 84), 'NERAZZURRI', font=big, fill=WHITE)
    d.text((56 + d.textlength('NERAZZURRI ', font=big), 84), 'DAILY', font=big, fill=SKY)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    im.quantize(32, method=Image.Quantize.MEDIANCUT).save(out, optimize=True)
    return out, os.path.getsize(out)
if __name__ == '__main__':
    print(*build(sys.argv[1] if len(sys.argv) > 1 else 'fonts'))
