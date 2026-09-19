#!/usr/bin/env python3
"""One-time: bring editions 1-9 (pre-Sept-14 anatomy, flattened tables) onto the Sept-19 design without re-authoring them."""
import re, sys, json, html
from bs4 import BeautifulSoup
sys.path.insert(0, 'tools'); import nd_render as R

def restyle(path):
    s = BeautifulSoup(open(path, encoding='utf-8').read(), 'lxml')
    n = int(re.search(r'edition-(\d+)', path).group(1))
    # stylesheet + top bar
    s.find('style').string = R.CSS
    top = s.select_one('.top'); a = top.find('a'); a['class'] = ['wm']
    for old in top.select('.util'): old.decompose()   # idempotent
    alt = s.select_one('img.mast')['alt']; dm = re.search(r'(\w+day), (\w+) (\d+), (\d{4})', alt)
    date = f"{dm.group(4)}-{R.MONTHS.index(dm.group(2))+1:02d}-{int(dm.group(3)):02d}"
    util = s.new_tag('span', attrs={'class':'util'}); util.append(f'Edition No. {n} · {R.shortdate(date)} · '); al = s.new_tag('a', href='/'); al.string = 'All editions'; util.append(al); top.append(util)
    # labels -> section heads; poll -> removed; sources -> panel; sign-off -> block
    sheet = s.select_one('.sheet')
    for lab in list(sheet.select('div.lab')):
        txt = lab.get_text(strip=True).rstrip(':'); head, _, meta = txt.partition(' · ')
        if head.startswith('THE POLL'):
            nxt = lab.find_next_sibling()
            while nxt is not None and nxt.get('class') == ['in'] and not nxt.find('table'):
                n2 = nxt.find_next_sibling(); nxt.decompose(); nxt = n2
            lab.decompose(); continue
        if head.startswith('SOURCES'):
            links_in = lab.find_next_sibling('div', class_='in')
            panel = s.new_tag('div', attrs={'class':'sources'}); sec = s.new_tag('div', attrs={'class':'sec'}); b = s.new_tag('b'); b.string = 'Sources'; sec.append(b)
            p = s.new_tag('p')
            first = True
            for a in links_in.select('a'):
                if not first: p.append(s.new_tag('br')); p.append('\n')
                first = False
                t = a.get_text(strip=True); outlet, sep, ttl = t.partition(' · ')
                na = s.new_tag('a', href=a['href'], rel='noopener')
                if sep: bb = s.new_tag('b'); bb.string = outlet; na.append(bb); na.append(' · ' + ttl)
                else: na.string = t
                p.append(na)
            panel.append(sec); panel.append(p); lab.replace_with(panel); links_in.decompose(); continue
        sec = s.new_tag('div', attrs={'class':'sec'}); b = s.new_tag('b'); b.string = head.title(); sec.append(b)
        if meta: em = s.new_tag('em'); em.string = meta; sec.append(em)
        lab.replace_with(sec)
    # sign-off paragraphs (between the last table/in and the sources panel)
    sign = s.new_tag('div', attrs={'class':'signoff'}); placed = False
    for d in list(sheet.select('div.in')):
        p = d.find('p')
        if not p or d.find('table'): continue
        txt = d.get_text(' ', strip=True)
        kind = ('note' if txt.startswith(('Kickoff times','Times are')) else 'ask' if txt.startswith('Reply') else 'fan' if txt.startswith('Fan-made')
                else 'next' if txt.startswith('NEXT EDITION') else 'follow' if txt.startswith('FOLLOW') else None)
        if not kind: continue
        if not placed: d.insert_before(sign); placed = True
        if kind == 'note': q = s.new_tag('p', attrs={'class':'note'}); q.append(BeautifulSoup(p.decode_contents(),'html.parser')); sign.append(q)
        elif kind == 'ask': q = s.new_tag('p', attrs={'class':'ask'}); q.append(BeautifulSoup(p.decode_contents(),'html.parser')); sign.append(q)
        elif kind == 'next':
            q = s.new_tag('div', attrs={'class':'next'}); b = s.new_tag('b'); b.string = 'Next edition'; sp = s.new_tag('span'); sp.string = txt.partition(':')[2].strip(); q.append(b); q.append(sp); sign.append(q)
        elif kind == 'follow':
            q = s.new_tag('p', attrs={'class':'follow'}); q.append('FOLLOW ')
            first = True
            for a in d.select('a'):
                if not first: q.append(' · ')
                first = False; na = s.new_tag('a', href=a['href'], rel='noopener'); na.string = a.get_text(strip=True); q.append(na)
            sign.append(q)
        d.decompose()
    foot = s.select_one('.foot')
    if foot and not foot.find('a', href='/subscribe/'):
        first = foot.find('a'); a = s.new_tag('a', href='/subscribe/'); a.string = 'Subscribe'
        first.insert_before(a); first.insert_before(' \u00b7 ')
    # canonical/favicon/h1 already present from the audit pass; make sure the foot sits last
    open(path, 'w', encoding='utf-8').write(str(s))
    title = s.title.get_text().split(' — ')[0]
    return {'n': n, 'date': date, 'title': html.unescape(title)}

if __name__ == '__main__':
    legacy = [restyle(p) for p in sys.argv[1:]]
    json.dump(legacy, open('data/legacy.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
    for e in legacy: print(e)
