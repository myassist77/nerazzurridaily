#!/usr/bin/env python3
"""Nerazzurri Daily renderer (design of Sept 19, 2026).
  python3 tools/nd_render.py data/edition-N.json           -> p/edition-N/index.html, build/email-N.html, build/edition-N.txt
  python3 tools/nd_render.py --index                        -> index.html, sitemap.xml (from data/*.json + data/legacy.json)
Run from the repo root. The masthead must already exist at assets/mast/edition-NN.png.
"""
import sys, os, re, json, html, glob, datetime

SITE = "https://www.nerazzurridaily.com"
MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"]
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@400;700&amp;family=Fragment+Mono&amp;display=swap" rel="stylesheet">'

CSS = """*{box-sizing:border-box}html{font-size:16px}
body{margin:0;background:#DCE3EF;font-family:Georgia,'Times New Roman',serif;color:#3D465C}
.sheet{max-width:700px;margin:0 auto;background:#fff}
.in{padding:0 28px}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.top{background:#06080F;padding:14px 28px;display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
.top a.wm{font-family:Oswald,sans-serif;font-weight:700;font-size:1.05rem;letter-spacing:.02em;color:#fff;text-decoration:none}
.top a.wm b{color:#8FB2F0;font-weight:700}
.top .util{font-family:'Fragment Mono',monospace;font-size:.82rem;color:#8FB2F0;letter-spacing:.02em}
.top .util a{color:#fff;text-decoration:underline;text-underline-offset:2px}
img.mast{display:block;width:100%;height:auto;border:0}
.dek{background:#EEF1F6;border-bottom:1px solid #C4CDDE;padding:14px 28px}
.dek p{margin:0;font-size:17px;line-height:1.6}
a{color:#0A2A66}
.bar{padding:7px 28px;margin-top:18px}
.bar.c{background:#2B5BB8}.bar.r{background:#8C4034}
.bar span{font-family:Oswald,sans-serif;font-weight:700;font-size:.95rem;color:#fff}
.bar em{font-family:'Fragment Mono',monospace;font-size:.82rem;color:#DCE3EF;font-style:normal}
.item{margin-top:14px;padding:2px 0 10px 6px;border-left:5px solid #2B5BB8;background:#EEF1F6}
.item.rep{border-left-color:#E7B4AE;background:#FBEAE7}
.item h3{font-family:Oswald,sans-serif;font-size:21px;font-weight:700;color:#0B1020;line-height:1.25;margin:12px 0 6px}
.item p{font-size:17px;line-height:1.6;margin:0 0 10px}
.kick{font-family:'Fragment Mono',monospace;font-size:.84rem;color:#2B5BB8;font-weight:700}
.item.rep .kick{color:#8C4034}
.sec{position:relative;margin:26px 28px 10px;padding-bottom:8px;border-bottom:1px solid #D8DFEC;display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}
.sec::after{content:"";position:absolute;left:0;bottom:-1px;width:36px;height:3px;background:#2B5BB8}
.sec b{font-family:Oswald,sans-serif;font-weight:700;font-size:15px;letter-spacing:.07em;text-transform:uppercase;color:#0B1020}
.sec em{font-family:'Fragment Mono',monospace;font-style:normal;font-size:.82rem;color:#5A647E;letter-spacing:.02em}
.sb{width:100%;border-collapse:collapse;margin:6px 0}
.sb td{padding:11px 0;border-bottom:1px solid #D8DFEC}
.sb .lbl{font-family:'Fragment Mono',monospace;font-size:.82rem;color:#5A647E;letter-spacing:.08em}
.sb .nm{font-family:Oswald,sans-serif;font-weight:700;font-size:18px;color:#0B1020;line-height:1.2;margin:2px 0 3px}
.chip{display:inline-block;vertical-align:2px;margin-left:8px;padding:1px 6px 0;border:1px solid #C4CDDE;border-radius:3px;font-family:'Fragment Mono',monospace;font-size:.72rem;font-weight:400;letter-spacing:.08em;color:#5A647E}
.sb .meta{font-family:'Fragment Mono',monospace;font-size:.82rem;color:#5A647E;line-height:1.6}
.sb .tm{font-family:'Fragment Mono',monospace;font-size:.82rem;color:#3D465C;line-height:1.6}
.sb .tm b{color:#0B1020;font-weight:700}
.signoff{padding:4px 28px 6px}
.signoff .note{font-family:'Fragment Mono',monospace;font-size:.82rem;color:#5A647E;line-height:1.6;margin:8px 0 0}
.signoff .ask{font-size:17px;line-height:1.6;margin:18px 0 0}
.signoff .next{margin-top:18px}
.signoff .next b{display:block;font-family:Oswald,sans-serif;font-size:13px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#2B5BB8;margin-bottom:2px}
.signoff .next span{font-family:Oswald,sans-serif;font-weight:700;font-size:18px;color:#0B1020;line-height:1.25}
.signoff .follow{font-family:'Fragment Mono',monospace;font-size:.82rem;color:#5A647E;margin:16px 0 0;letter-spacing:.02em}
.signoff .follow a{color:#0A2A66}
.sources{background:#EEF1F6;margin-top:22px;padding:2px 28px 18px}
.sources .sec{margin-left:0;margin-right:0;margin-top:16px}
.sources p{font-family:'Fragment Mono',monospace;font-size:.82rem;line-height:1.8;margin:6px 0 0;color:#3D465C}
.sources a{color:#0A2A66;text-decoration:none;border-bottom:1px solid #C4CDDE}
.sources a b{color:#0B1020;font-weight:700}
.foot{background:#DCE3EF;padding:18px 28px;font-family:'Fragment Mono',monospace;font-size:.84rem;color:#5A647E;line-height:1.9}
.foot a{display:inline-block}
.idx{padding:8px 28px 28px}
.idx h1{font-family:Oswald,sans-serif;font-size:30px;color:#0B1020;margin:22px 0 4px}
.idx .sub{font-size:17px;margin:0 0 20px}
.idx ul{list-style:none;padding:0;margin:0}
.idx li{padding:13px 0;border-bottom:1px solid #D8DFEC}
.idx .d{font-family:'Fragment Mono',monospace;font-size:.82rem;color:#5A647E}
.idx .t{font-family:Oswald,sans-serif;font-size:1.12rem;font-weight:700;color:#0B1020;text-decoration:none;display:block;margin-top:3px}
@media(max-width:520px){.in,.dek,.bar,.top,.foot,.idx,.signoff,.sources{padding-left:16px;padding-right:16px}.sec{margin-left:16px;margin-right:16px}.sources .sec{margin-left:0;margin-right:0}}"""

def esc(x): return html.escape(str(x), quote=True)
def longdate(iso):
    d = datetime.date.fromisoformat(iso); return f"{d.strftime('%A')}, {MONTHS[d.month-1]} {d.day}, {d.year}"
def shortdate(iso):
    d = datetime.date.fromisoformat(iso); return f"{d.strftime('%a')}, {MONTHS[d.month-1][:3]} {d.day}"
def nbsp(s): return s.replace('\xa0', '&nbsp;')
def et_bold(line):  # "12:00 PM ET · ..." -> ET time bold
    return re.sub(r'^(\d{1,2}:\d{2}(?:\xa0|&nbsp;| )[AP]M(?:\xa0|&nbsp;| )ET)', r'<b>\1</b>', line)
def chip(name, venue):
    return esc(name) + (f'<span class="chip">{venue}</span>' if venue else '')
def head_case(s):  # LATEST RESULT -> Latest result (CSS uppercases on the page; email needs real caps)
    return s

# ------------------------------------------------------------------ page
def page_blocks(d):
    out = []; in_signoff = False
    def close():
        nonlocal in_signoff
        if in_signoff: out.append('</div>'); in_signoff = False
    for b in d['blocks']:
        t = b['t']
        if t not in ('note','ask','next','follow'): close()
        if t == 'dek': out.append(f'<div class="dek"><p>{b["html"]}</p></div>')
        elif t == 'scoreboard':
            rows = ''.join(f'<tr><td><div class="lbl">{esc(r["label"])}</div><div class="nm">{chip(r["name"], r.get("venue"))}</div>'
                           f'<div class="tm">{et_bold(nbsp(r["line"]))}</div></td></tr>' for r in b['rows'])
            out.append(f'<div class="in"><table class="sb"><tbody>{rows}</tbody></table></div>')
        elif t == 'bar': out.append(f'<div class="bar {b["kind"]}"><span>{esc(b["label"])}</span> <em>· {esc(b["sub"])}</em></div>')
        elif t == 'item':
            paras = ''.join(f'<p>{p}</p>' for p in b['paras'])
            out.append(f'<div class="item{" rep" if b.get("rep") else ""}"><div class="in"><h3>{b["h3"]}</h3>{paras}<p class="kick">{b["kicker"]}</p></div></div>')
        elif t == 'section':
            out.append(f'<div class="sec"><b>{esc(b["head"])}</b>' + (f'<em>{esc(b["meta"])}</em>' if b.get('meta') else '') + '</div>')
        elif t == 'fixtures':
            rows = ''.join(f'<tr><td><div class="nm">{chip(r["name"], r.get("venue"))}</div><div class="meta">{nbsp(r["line2"])}</div>'
                           f'<div class="tm">{et_bold(nbsp(r["line3"]))}</div></td></tr>' for r in b['rows'])
            out.append(f'<div class="in"><table class="sb"><tbody>{rows}</tbody></table></div>')
        elif t in ('note','ask','next','follow'):
            if not in_signoff: out.append('<div class="signoff">'); in_signoff = True
            if t == 'note': out.append(f'<p class="note">{b["html"]}</p>')
            elif t == 'ask': out.append(f'<p class="ask">{b["html"]}</p>')
            elif t == 'next': out.append(f'<div class="next"><b>Next edition</b><span>{esc(b["text"])}</span></div>')
            elif t == 'follow':
                links = ' · '.join(f'<a href="{esc(l["url"])}" rel="noopener">{esc(l["label"])}</a>' for l in b['links'])
                out.append(f'<p class="follow">FOLLOW {links}</p>')
        elif t == 'sources':
            links = '<br>\n'.join(f'<a href="{esc(l["url"])}" rel="noopener">' + (f'<b>{esc(l["outlet"])}</b> · ' if l.get('outlet') else '') + f'{esc(l["title"])}</a>' for l in b['links'])
            out.append(f'<div class="sources"><div class="sec"><b>Sources</b></div><p>{links}</p></div>')
        elif t == 'p': out.append(f'<div class="in"><p>{b["html"]}</p></div>')
        elif t == 'poll': pass   # dropped from the design on Sept 19, 2026; kept in the JSON as history
    close()
    return ''.join(out)

def render_page(d):
    n = d['n']; title = d['title']; desc = d['description']; ld = longdate(d['date'])
    alt = d.get('mast_alt') or f"Nerazzurri Daily Edition No. {n}, {ld} — {title}"
    head = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<title>{esc(title)} — Nerazzurri Daily No. {n}</title><link rel="canonical" href="{SITE}/p/edition-{n}/"><link rel="icon" href="/favicon.svg" type="image/svg+xml">'
            f'<meta name="description" content="{esc(desc)}">\n<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">\n'
            f'<meta property="og:type" content="article"><meta property="og:image" content="{SITE}/assets/mast/edition-{n:02d}.png">\n{FONTS}\n<style>{CSS}</style></head>')
    body = (f'<body><div class="sheet">\n<div class="top"><a class="wm" href="/">NERAZZURRI <b>DAILY</b></a><span class="util">Edition No. {n} · {shortdate(d["date"])} · <a href="/">All editions</a></span></div>'
            f'<h1 class="sr">{esc(title)}</h1><img class="mast" src="/assets/mast/edition-{n:02d}.png" alt="{esc(alt)}">'
            + page_blocks(d) +
            '<div class="foot">Fan-made. Not affiliated with FC Internazionale Milano.<br>\n<a href="/">All editions</a> &middot; <a href="https://www.youtube.com/@nerazzurridaily" rel="noopener">YouTube</a> &middot; <a href="https://www.tiktok.com/@nerazzurridaily" rel="noopener">TikTok</a></div>\n</div></body></html>\n')
    return head + body

# ------------------------------------------------------------------ email (tables + inline styles, 644px)
SANS = "Arial,Helvetica,sans-serif"; SERF = "Georgia,'Times New Roman',serif"; MONO = "'Courier New',Courier,monospace"
def P(h, size=17, color='#3D465C', mt=0, mb=10, fam=SERF, weight='normal', lh='1.6', extra=''):
    return f'<p style="margin:{mt}px 0 {mb}px;font-family:{fam};font-size:{size}px;line-height:{lh};color:{color};font-weight:{weight};{extra}">{h}</p>'
def sec_email(head, meta=None):
    return (f'<tr><td style="padding:24px 28px 0;background:#ffffff;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>'
            f'<td style="padding:0 0 8px;border-bottom:1px solid #D8DFEC;"><span style="font-family:{SANS};font-weight:bold;font-size:14px;letter-spacing:1px;color:#0B1020;">{esc(head).upper()}</span>'
            + (f' &nbsp;<span style="font-family:{MONO};font-size:13px;color:#5A647E;">{esc(meta)}</span>' if meta else '') +
            f'</td></tr><tr><td style="padding:0;font-size:0;line-height:0;height:3px;"><table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr><td width="36" height="3" style="background:#2B5BB8;font-size:0;line-height:0;">&nbsp;</td></tr></table></td></tr></table></td></tr>')
def chip_email(name, venue):
    return esc(name) + (f' <span style="display:inline-block;vertical-align:2px;margin-left:6px;padding:1px 5px 0;border:1px solid #C4CDDE;border-radius:3px;font-family:{MONO};font-size:11px;letter-spacing:1px;color:#5A647E;">{venue}</span>' if venue else '')
def row_email(lines):
    return f'<tr><td style="padding:11px 0;border-bottom:1px solid #D8DFEC;">{"".join(lines)}</td></tr>'
def render_email(d, absolute_links=True):
    n = d['n']; rows = []
    def R(h, bg='#ffffff', pad='0 28px'): rows.append(f'<tr><td style="background:{bg};padding:{pad};">{h}</td></tr>')
    R(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td style="font-family:{SANS};font-weight:bold;font-size:17px;letter-spacing:.4px;color:#ffffff;">NERAZZURRI <span style="color:#8FB2F0;">DAILY</span></td>'
      f'<td align="right" style="font-family:{MONO};font-size:13px;color:#8FB2F0;">Edition No. {n} · {shortdate(d["date"])} · <a href="{SITE}/p/edition-{n}/" style="color:#ffffff;text-decoration:underline;">View online</a></td></tr></table>', '#06080F', '14px 28px')
    rows.append(f'<tr><td style="padding:0;font-size:0;line-height:0;"><img src="{SITE}/assets/mast/edition-{n:02d}.png" width="644" alt="{esc(d.get("mast_alt",""))}" style="display:block;width:100%;max-width:644px;height:auto;border:0;"></td></tr>')
    in_signoff = False
    for b in d['blocks']:
        t = b['t']
        if in_signoff and t not in ('note','ask','next','follow'): rows.append('</td></tr>'); in_signoff = False
        if t == 'dek': R(P(b['html']), '#EEF1F6', '16px 28px')
        elif t == 'scoreboard':
            trs = ''.join(row_email([f'<div style="font-family:{MONO};font-size:13px;letter-spacing:1px;color:#5A647E;">{esc(r["label"])}</div>',
                                     f'<div style="font-family:{SANS};font-weight:bold;font-size:18px;color:#0B1020;line-height:1.2;margin:2px 0 3px;">{chip_email(r["name"], r.get("venue"))}</div>',
                                     f'<div style="font-family:{MONO};font-size:13px;color:#3D465C;line-height:1.6;">{et_bold(nbsp(r["line"])).replace("<b>", "<b style=\'color:#0B1020\'>")}</div>']) for r in b['rows'])
            R(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:6px 0;">{trs}</table>')
        elif t == 'bar':
            bg = '#8C4034' if b['kind']=='r' else '#2B5BB8'
            rows.append('<tr><td style="height:18px;line-height:18px;font-size:0;">&nbsp;</td></tr>')
            R(f'<span style="font-family:{SANS};font-weight:bold;font-size:14px;color:#ffffff;letter-spacing:.5px;">{esc(b["label"])}</span> <span style="font-family:{MONO};font-size:13px;color:#DCE3EF;">· {esc(b["sub"])}</span>', bg, '8px 28px')
        elif t == 'item':
            rep = b.get('rep'); bd = '#E7B4AE' if rep else '#2B5BB8'; bg = '#FBEAE7' if rep else '#EEF1F6'; kc = '#8C4034' if rep else '#2B5BB8'
            inner = (f'<h3 style="margin:12px 0 6px;font-family:{SANS};font-size:21px;font-weight:bold;color:#0B1020;line-height:1.25;">{b["h3"]}</h3>'
                     + ''.join(P(p) for p in b['paras']) + P(b['kicker'], 13, kc, 0, 2, MONO, 'bold', '1.5'))
            rows.append(f'<tr><td style="padding:14px 28px 0;background:#ffffff;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td style="background:{bg};border-left:5px solid {bd};padding:2px 14px 6px;">{inner}</td></tr></table></td></tr>')
        elif t == 'section': rows.append(sec_email(b['head'], b.get('meta')))
        elif t == 'fixtures':
            trs = ''.join(row_email([f'<div style="font-family:{SANS};font-weight:bold;font-size:18px;color:#0B1020;line-height:1.2;margin:0 0 3px;">{chip_email(r["name"], r.get("venue"))}</div>',
                                     f'<div style="font-family:{MONO};font-size:13px;color:#5A647E;line-height:1.6;">{nbsp(r["line2"])}</div>',
                                     f'<div style="font-family:{MONO};font-size:13px;color:#3D465C;line-height:1.6;">{et_bold(nbsp(r["line3"])).replace("<b>", "<b style=\'color:#0B1020\'>")}</div>']) for r in b['rows'])
            R(f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:6px 0;">{trs}</table>')
        elif t in ('note','ask','next','follow'):
            if not in_signoff: rows.append('<tr><td style="background:#ffffff;padding:4px 28px 6px;">'); in_signoff = True
            if t == 'note': rows.append(P(b['html'], 13, '#5A647E', 8, 0, MONO))
            elif t == 'ask': rows.append(P(b['html'], 17, '#3D465C', 18, 0))
            elif t == 'next': rows.append(f'<div style="margin-top:18px;"><div style="font-family:{SANS};font-size:13px;font-weight:bold;letter-spacing:1.5px;color:#2B5BB8;margin-bottom:2px;">NEXT EDITION</div><div style="font-family:{SANS};font-weight:bold;font-size:18px;color:#0B1020;line-height:1.25;">{esc(b["text"])}</div></div>')
            elif t == 'follow':
                links = ' · '.join(f'<a href="{esc(l["url"])}" style="color:#0A2A66;">{esc(l["label"])}</a>' for l in b['links'])
                rows.append(P('FOLLOW ' + links, 13, '#5A647E', 16, 0, MONO))
        elif t == 'sources':
            links = '<br>\n'.join(f'<a href="{esc(l["url"])}" style="color:#0A2A66;text-decoration:none;border-bottom:1px solid #C4CDDE;">' + (f'<b style="color:#0B1020;">{esc(l["outlet"])}</b> · ' if l.get('outlet') else '') + f'{esc(l["title"])}</a>' for l in b['links'])
            rows.append(f'<tr><td style="background:#EEF1F6;padding:2px 28px 18px;margin-top:22px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td style="padding:16px 0 8px;border-bottom:1px solid #D8DFEC;"><span style="font-family:{SANS};font-weight:bold;font-size:14px;letter-spacing:1px;color:#0B1020;">SOURCES</span></td></tr>'
                        f'<tr><td style="padding:0;font-size:0;line-height:0;height:3px;"><table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr><td width="36" height="3" style="background:#2B5BB8;font-size:0;line-height:0;">&nbsp;</td></tr></table></td></tr></table>'
                        + P(links, 13, '#3D465C', 8, 0, MONO, 'normal', '1.8') + '</td></tr>')
        elif t == 'p': R(P(b['html']), '#ffffff', '2px 28px')
    if in_signoff: rows.append('</td></tr>')
    R(f'<div style="font-family:{MONO};font-size:13px;color:#5A647E;line-height:1.9;">Fan-made. Not affiliated with FC Internazionale Milano.<br><a href="{SITE}/" style="color:#0A2A66;">All editions</a> &middot; <a href="https://www.youtube.com/@nerazzurridaily" style="color:#0A2A66;">YouTube</a> &middot; <a href="https://www.tiktok.com/@nerazzurridaily" style="color:#0A2A66;">TikTok</a></div>', '#DCE3EF', '18px 28px')
    R(f'<div style="font-family:{MONO};font-size:13px;color:#4A5470;line-height:1.8;text-align:center;">You are receiving this because you subscribed to Nerazzurri Daily.<br><a href="{{{{ unsubscribe }}}}" style="color:#4A5470;text-decoration:underline;">Unsubscribe</a> &middot; <a href="{SITE}/p/edition-{n}/" style="color:#4A5470;text-decoration:underline;">Read online</a></div>', '#DCE3EF', '0 28px 24px')
    return (f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n<title>{esc(d["title"])}</title></head>\n'
            f'<body style="margin:0;padding:0;background:#DCE3EF;">\n<div style="display:none;max-height:0;overflow:hidden;opacity:0;">{esc(d["description"])}</div>\n'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#DCE3EF;"><tr><td align="center" style="padding:0;">\n'
            f'<table role="presentation" width="644" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:644px;background:#ffffff;">\n{"".join(rows)}\n</table>\n</td></tr></table>\n</body></html>')

# ------------------------------------------------------------------ text (for nd_checks)
def render_text(d):
    from bs4 import BeautifulSoup
    lines = [d['title'], '']
    for b in d['blocks']:
        t = b['t']
        if t == 'dek': lines += [BeautifulSoup(b['html'],'html.parser').get_text(), '']
        elif t == 'scoreboard': lines += [f"{r['label']}\n{r['name']}{'  '+r['venue'] if r.get('venue') else ''}\n{r['line']}" for r in b['rows']] + ['']
        elif t == 'bar': lines += [f"{b['label']} · {b['sub']}"]
        elif t == 'item':
            lines += ['### ' + BeautifulSoup(b['h3'],'html.parser').get_text()] + [BeautifulSoup(p,'html.parser').get_text() for p in b['paras']] + [BeautifulSoup(b['kicker'],'html.parser').get_text(), '']
        elif t == 'section': lines += [b['head'] + (' · ' + b['meta'] if b.get('meta') else '')]
        elif t == 'fixtures': lines += [f"{r['name']}{'  '+r['venue'] if r.get('venue') else ''}\n{r['line2']}\n{r['line3']}" for r in b['rows']] + ['']
        elif t in ('note','ask','p'): lines += [BeautifulSoup(b['html'],'html.parser').get_text(), '']
        elif t == 'next': lines += ['NEXT EDITION: ' + b['text']]
        elif t == 'follow': lines += ['FOLLOW · ' + ' · '.join(l['label'] for l in b['links']), '']
        elif t == 'sources': lines += ['SOURCES:'] + [(l['outlet'] + ' · ' if l.get('outlet') else '') + l['title'] for l in b['links']]
    lines += ['', 'Fan-made. Not affiliated with FC Internazionale Milano.']
    return '\n'.join(lines).replace('\xa0', ' ')

# ------------------------------------------------------------------ index + sitemap
def build_index():
    eds = []
    for p in glob.glob('data/edition-*.json'):
        d = json.load(open(p, encoding='utf-8')); eds.append((d['n'], d['date'], d['title']))
    if os.path.exists('data/legacy.json'):
        for e in json.load(open('data/legacy.json', encoding='utf-8')): eds.append((e['n'], e['date'], e['title']))
    eds = sorted({e[0]: e for e in eds}.values(), key=lambda e: -e[0])
    lis = ''.join(f'<li><span class="d">No. {n} &middot; {longdate(dt)}</span><a class="t" href="p/edition-{n}/">{esc(t)}</a></li>' for n, dt, t in eds)
    page = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<title>Nerazzurri Daily — every edition</title><link rel="canonical" href="{SITE}/"><link rel="icon" href="/favicon.svg" type="image/svg+xml">'
            f'<meta name="description" content="Inter Milan in English, every morning — sorted into what is confirmed and what is only reported. Every edition of Nerazzurri Daily.">\n'
            f'<meta property="og:title" content="Nerazzurri Daily — every edition"><meta property="og:image" content="{SITE}/assets/mast/edition-{eds[0][0]:02d}.png">\n{FONTS}\n<style>{CSS}</style></head>'
            f'<body><div class="sheet">\n<div class="top"><a class="wm" href="./">NERAZZURRI <b>DAILY</b></a><span class="util">{len(eds)} editions · since Sep 2, 2026</span></div>'
            f'<div class="idx"><h1>Every edition</h1><p class="sub">Inter Milan in English, every morning — sorted into what is confirmed and what is only reported.</p><ul>{lis}</ul></div>'
            '<div class="foot">Fan-made. Not affiliated with FC Internazionale Milano.<br>\n<a href="./">All editions</a> &middot; <a href="https://www.youtube.com/@nerazzurridaily" rel="noopener">YouTube</a> &middot; <a href="https://www.tiktok.com/@nerazzurridaily" rel="noopener">TikTok</a></div>\n</div></body></html>\n')
    open('index.html', 'w', encoding='utf-8').write(page)
    urls = [(f'{SITE}/', eds[0][1])] + [(f'{SITE}/p/edition-{n}/', dt) for n, dt, _ in eds]
    open('sitemap.xml', 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'  <url><loc>{u}</loc><lastmod>{dt}</lastmod></url>\n' for u, dt in urls) + '</urlset>\n')
    return len(eds)

if __name__ == '__main__':
    if '--index' in sys.argv: print('index + sitemap:', build_index(), 'editions'); sys.exit()
    for p in [a for a in sys.argv[1:] if a.endswith('.json')]:
        d = json.load(open(p, encoding='utf-8')); n = d['n']
        # a plain paragraph right after the fixtures table is the kickoff note
        for i, b in enumerate(d['blocks']):
            if b['t'] == 'p' and i and d['blocks'][i-1]['t'] == 'fixtures': b['t'] = 'note'
        os.makedirs(f'p/edition-{n}', exist_ok=True); os.makedirs('build', exist_ok=True)
        open(f'p/edition-{n}/index.html', 'w', encoding='utf-8').write(render_page(d))
        open(f'build/email-{n}.html', 'w', encoding='utf-8').write(render_email(d))
        open(f'build/edition-{n}.txt', 'w', encoding='utf-8').write(render_text(d))
        assert os.path.exists(f'assets/mast/edition-{n:02d}.png'), f'missing masthead assets/mast/edition-{n:02d}.png'
        print(f'edition {n}: page, build/email-{n}.html, build/edition-{n}.txt')
