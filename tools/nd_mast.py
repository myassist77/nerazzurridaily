#!/usr/bin/env python3
"""Masthead: 640x350 palette PNG under 7,000 bytes.
  python3 tools/nd_mast.py --n 19 --date 2026-09-20 --line1 "WHAT HAPPENED" --line2 "AT THE OLIMPICO" --out assets/mast/edition-19.png
Fails (exit 1) if the wordmark wraps, the headline is not exactly two lines, the headline bottom passes 322px,
any block runs under the sleeve (right edge > 556), the fonts did not load, or the PNG is not under 7,000 bytes.
Needs: pip install playwright pillow && python3 -m playwright install chromium ; network for Google Fonts."""
import argparse, asyncio, datetime, io, json, sys
from PIL import Image
from playwright.async_api import async_playwright
MONTHS=["January","February","March","April","May","June","July","August","September","October","November","December"]
PALETTE=[(0x06,0x08,0x0F),(0x0F,0x15,0x26),(0x4A,0x7B,0xE0),(0xFF,0xFF,0xFF),(0x8F,0xB2,0xF0),(0xA9,0xB3,0xC9),(0x6A,0x72,0x80)]  # 7: brand + one mid-grey for antialiasing
W=[9,6,12,6,9,6,12,8]
def html(eyebrow,l1,l2):
    bars=''; acc=0
    for i,w in enumerate(W): bars+=f'<i style="position:absolute;left:{acc}px;top:0;width:{w}px;height:100%;background:{"#0F1526" if i%2==0 else "#4A7BE0"}"></i>'; acc+=w
    return f'''<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Anton&family=IBM+Plex+Mono:wght@500&display=block">
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{background:#222}}
#m{{width:640px;height:350px;background:#06080F;position:relative;overflow:hidden;padding:30px 36px 28px;color:#fff}}
#sleeve{{position:absolute;right:0;top:0;width:68px;height:350px;overflow:hidden}}
.blk{{max-width:520px;position:relative}}
#eyebrow{{font-family:'IBM Plex Mono',monospace;font-weight:500;font-size:19px;letter-spacing:.14em;text-transform:uppercase;color:#A9B3C9;line-height:1.35}}
#word{{font-family:Anton,sans-serif;font-size:72px;line-height:.92;margin-top:14px;white-space:nowrap;color:#FFFFFF}}#word b{{font-weight:400;color:#8FB2F0}}
#head{{font-family:Anton,sans-serif;font-size:64px;line-height:.96;margin-top:26px;text-transform:uppercase;color:#FFFFFF}}
</style></head><body><div id="m"><div id="sleeve">{bars}</div><div class="blk" id="eyebrow">{eyebrow}</div>
<div class="blk" id="word">NERAZZURRI <b>DAILY</b></div><div class="blk" id="head">{l1}<br>{l2}</div></div></body></html>'''
MEASURE='''() => { const root=document.getElementById('m').getBoundingClientRect(); const o={};
 for (const id of ['eyebrow','word','head']) { const e=document.getElementById(id); const r=e.getBoundingClientRect(); const lh=parseFloat(getComputedStyle(e).lineHeight);
   o[id]={top:r.top-root.top,bottom:r.bottom-root.top,right:r.left-root.left+e.scrollWidth,h:r.height,lines:Math.round(r.height/lh)}; }
 o.fonts={anton:document.fonts.check('72px Anton'),mono:document.fonts.check("500 19px 'IBM Plex Mono'")}; return o; }'''
async def build(a):
    d=datetime.date.fromisoformat(a.date)
    eyebrow=f"Edition No. {a.n} · {d.strftime('%A')}, {MONTHS[d.month-1]} {d.day}, {d.year} · 90 seconds"
    async with async_playwright() as p:
        b=await p.chromium.launch(args=["--no-sandbox"]); pg=await b.new_page(viewport={"width":800,"height":500},device_scale_factor=1)
        await pg.set_content(html(eyebrow,a.line1,a.line2),wait_until="load"); await pg.evaluate("document.fonts.ready"); await pg.wait_for_timeout(400)
        m=await pg.evaluate(MEASURE); fails=[]
        if not (m['fonts']['anton'] and m['fonts']['mono']): fails.append('fonts did not load')
        if m['word']['lines']!=1: fails.append(f"wordmark is {m['word']['lines']} lines")
        if m['head']['lines']!=2: fails.append(f"headline is {m['head']['lines']} lines (must be 2)")
        if m['head']['bottom']>322: fails.append(f"headline bottom {m['head']['bottom']:.0f} > 322")
        for k in ('eyebrow','word','head'):
            if m[k]['right']>556: fails.append(f"{k} right edge {m[k]['right']:.0f} > 556 (under the sleeve)")
        png=await pg.locator('#m').screenshot(); await b.close()
    im=Image.open(io.BytesIO(png)).convert('RGB')
    pal=Image.new('P',(1,1)); flat=sum(PALETTE,()); pal.putpalette(list(flat)+[0]*(768-len(flat)))
    q=im.quantize(palette=pal,dither=Image.Dither.NONE)
    buf=io.BytesIO(); q.save(buf,'PNG',optimize=True); size=buf.tell()
    if size>=7000: fails.append(f"PNG is {size} bytes (must be under 7,000) — shorten the headline")
    report={'eyebrow':eyebrow,'measure':m,'bytes':size,'colors':len(q.getcolors()),'fails':fails}
    print(json.dumps(report,indent=1))
    if fails: print('MASTHEAD BUILD FAILED: '+'; '.join(fails),file=sys.stderr); sys.exit(1)
    open(a.out,'wb').write(buf.getvalue()); print('MASTHEAD BUILD OK ->',a.out,size,'bytes')
ap=argparse.ArgumentParser(); ap.add_argument('--n',type=int,required=True); ap.add_argument('--date',required=True)
ap.add_argument('--line1',required=True); ap.add_argument('--line2',required=True); ap.add_argument('--out',required=True)
asyncio.run(build(ap.parse_args()))
