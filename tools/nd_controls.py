#!/usr/bin/env python3
"""Controls A1/A2/A3 measured with Playwright on the rendered page and email.
  python3 tools/nd_controls.py --n 19 [--port 8765]   (serves the repo root itself; masthead read from assets/)
Writes build/controls-N.json and build/shot-N-{page,email}-{700,390}.png plus small JPEG crops for the reviewer:
build/crop-N-email-390-top.jpg, build/crop-N-email-390-bottom.jpg. Exit 1 on any failure."""
import argparse, asyncio, io, json, os, re, subprocess, sys, time
from PIL import Image
from playwright.async_api import async_playwright

def lum(hexs):
    r,g,b=[int(hexs[i:i+2],16)/255 for i in (1,3,5)]
    f=lambda c: c/12.92 if c<=0.03928 else ((c+0.055)/1.055)**2.4
    return 0.2126*f(r)+0.7152*f(g)+0.0722*f(b)
def ratio(a,b):
    la,lb=lum(a),lum(b); hi,lo=max(la,lb),min(la,lb); return (hi+0.05)/(lo+0.05)

JS_TEXT = r'''() => {
 const toHex = c => { const m=c.match(/\d+/g); if(!m) return null; const [r,g,b,a]=m.map(Number); if(a===0) return null; return '#'+[r,g,b].map(x=>x.toString(16).padStart(2,'0')).join('').toUpperCase(); };
 const bg = el => { let e=el; while(e){ const c=getComputedStyle(e).backgroundColor; const h=toHex(c); if(h) return h; e=e.parentElement; } return '#FFFFFF'; };
 const out=[]; const walker=document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
 let node; while((node=walker.nextNode())){ const t=node.textContent.trim(); if(!t) continue; const el=node.parentElement; const cs=getComputedStyle(el); if(cs.display==='none'||cs.visibility==='hidden') continue;
   const r=el.getBoundingClientRect(); if(r.width===0||r.height===0) continue;
   out.push({text:t.slice(0,30), fs:parseFloat(cs.fontSize), fam:cs.fontFamily.split(',')[0].replace(/['"]/g,''), color:toHex(cs.color), bg:bg(el), link:!!el.closest('a'), tag:el.tagName.toLowerCase(), cls:el.className||''}); }
 return out; }'''

async def run(a):
    os.makedirs('build', exist_ok=True)
    srv = subprocess.Popen([sys.executable,'-m','http.server',str(a.port)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(0.8)
    try:
        email = open(f'build/email-{a.n}.html', encoding='utf-8').read().replace('https://www.nerazzurridaily.com/assets/', f'http://localhost:{a.port}/assets/')
        open(f'build/_email-{a.n}-local.html','w',encoding='utf-8').write(email)
        res = {'n': a.n, 'fails': [], 'warns': []}
        async with async_playwright() as p:
            b = await p.chromium.launch(args=["--no-sandbox"])
            for kind, url in (('page', f'http://localhost:{a.port}/p/edition-{a.n}/'), ('email', f'http://localhost:{a.port}/build/_email-{a.n}-local.html')):
                for w in (700, 390):
                    pg = await b.new_page(viewport={"width": w, "height": 900})
                    await pg.goto(url, wait_until="networkidle"); await pg.wait_for_timeout(300)
                    sw = await pg.evaluate("document.documentElement.scrollWidth")
                    k = f'{kind}-{w}'; res[k] = {'scrollWidth': sw}
                    if sw > w: res['fails'].append(f"A1 {k}: horizontal overflow {sw}px > {w}px")
                    mast = await pg.evaluate("(()=>{const i=document.querySelector('img[alt*=\"Nerazzurri Daily Edition\"]')||document.querySelector('img'); if(!i) return null; const r=i.getBoundingClientRect(); return {w:r.width,h:r.height,natural:i.naturalWidth,complete:i.complete}})()")
                    res[k]['masthead'] = mast
                    if not mast or not mast['complete'] or mast['natural'] == 0: res['fails'].append(f"G {k}: masthead image did not load")
                    if w == 390 and mast:
                        scale = mast['w'] / 640; head_px = 64 * scale
                        h3 = await pg.evaluate("(()=>{const h=document.querySelector('h3'); return h?parseFloat(getComputedStyle(h).fontSize):null})()")
                        res[k]['A3'] = {'masthead_width': round(mast['w'],1), 'scale': round(scale,3), 'headline_px': round(head_px,1), 'h3_px': h3, 'ratio': round(head_px/(h3 or 21),2)}
                        if h3 and head_px / h3 < 1.6: res['fails'].append(f"A3 {k}: masthead headline {head_px:.0f}px vs h3 {h3}px = {head_px/h3:.2f}x < 1.6x")
                    texts = await pg.evaluate(JS_TEXT)
                    small = [t for t in texts if t['fs'] < 13 and 'chip' not in t['cls'] and not re.match(r'^(HOME|AWAY)$', t['text'])]
                    res[k]['min_font_px'] = min((t['fs'] for t in texts), default=None)
                    if small and w == 390: res['fails'].append(f"A3 {k}: {len(small)} text runs under 13px, e.g. '{small[0]['text']}' {small[0]['fs']}px")
                    pairs = {}
                    for t in texts:
                        if t['color'] and t['bg']: key = (t['color'], t['bg']); pairs.setdefault(key, {'ratio': round(ratio(*key),2), 'link': t['link'], 'n': 0, 'eg': t['text']}); pairs[key]['n'] += 1
                    worst = min(pairs.values(), key=lambda x: x['ratio']) if pairs else None
                    res[k]['A2'] = {'pairs': len(pairs), 'min_ratio': worst['ratio'] if worst else None, 'min_pair_example': worst['eg'] if worst else None,
                                    'min_link_ratio': min([v['ratio'] for v in pairs.values() if v['link']], default=None)}
                    for (fg, bgc), v in pairs.items():
                        if v['ratio'] < 4.5: res['fails'].append(f"A2 {k}: {fg} on {bgc} = {v['ratio']}:1 ('{v['eg']}')")
                    shot = f'build/shot-{a.n}-{kind}-{w}.png'; await pg.screenshot(path=shot, full_page=True)
                    if kind == 'email' and w == 390:
                        im = Image.open(shot).convert('RGB'); H = im.size[1]
                        for name, box in (('top', (0, 0, 390, min(1300, H))), ('bottom', (0, max(0, H-1300), 390, H))):
                            c = im.crop(box).resize((300, int((box[3]-box[1])*300/390))); c.save(f'build/crop-{a.n}-email-390-{name}.jpg', 'JPEG', quality=45, optimize=True)
                    await pg.close()
            await b.close()
        json.dump(res, open(f'build/controls-{a.n}.json','w'), indent=1)
        print(json.dumps({k: v for k, v in res.items() if k in ('fails','warns','email-390','page-390')}, indent=1))
        print('CONTROLS', 'FAILED' if res['fails'] else 'PASSED')
        sys.exit(1 if res['fails'] else 0)
    finally:
        srv.terminate()

ap = argparse.ArgumentParser(); ap.add_argument('--n', type=int, required=True); ap.add_argument('--port', type=int, default=8765)
asyncio.run(run(ap.parse_args()))
