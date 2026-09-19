#!/usr/bin/env python3
"""Archive page (Sept-14-2026 anatomy, editions 10+) -> edition JSON. One-time migration + reference for the schema."""
import re, sys, json, html
from bs4 import BeautifulSoup, NavigableString

def inner(el): return el.decode_contents().strip() if el else ''
def split_br(s): return [p.strip() for p in re.split(r'<br\s*/?>', s) if p.strip()]
def name_venue(s):
    m = re.match(r'(.*?)(?:\s|&nbsp;|\xa0){2,}(HOME|AWAY)$', s.replace('\xa0',' '))
    return (m.group(1).strip(), m.group(2)) if m else (s.replace('\xa0',' ').strip(), None)

def extract(path):
    s = BeautifulSoup(open(path, encoding='utf-8').read(), 'lxml')
    n = int(re.search(r'edition-(\d+)', path).group(1))
    title = s.title.get_text().split(' — ')[0]
    desc = s.find('meta', attrs={'name':'description'})['content']
    alt = s.select_one('img.mast')['alt']
    dm = re.search(r'(\w+day), (\w+) (\d+), (\d{4})', alt)
    months = ["January","February","March","April","May","June","July","August","September","October","November","December"]
    date = f"{dm.group(4)}-{months.index(dm.group(2))+1:02d}-{int(dm.group(3)):02d}"
    blocks = []
    kids = [c for c in s.select_one('.sheet').children if getattr(c,'name',None)]
    i = 0
    while i < len(kids):
        c = kids[i]; cls = c.get('class', [])
        if c.name in ('h1','img') or 'top' in cls or 'foot' in cls: i += 1; continue
        if 'dek' in cls: blocks.append({'t':'dek','html':inner(c.find('p'))})
        elif 'bar' in cls:
            blocks.append({'t':'bar','kind':'r' if 'r' in cls else 'c','label':c.find('span').get_text(strip=True),'sub':c.find('em').get_text(strip=True).lstrip('· ').strip()})
        elif 'item' in cls:
            parts = [k for k in c.select_one('.in').children if getattr(k,'name',None)]
            it = {'t':'item','rep':'rep' in cls,'h3':inner(parts[0]),'paras':[],'kicker':''}
            for k in parts[1:]:
                if k.name=='p' and 'kick' in k.get('class',[]): it['kicker'] = inner(k)
                elif k.name=='p': it['paras'].append(inner(k))
            blocks.append(it)
        elif 'lab' in cls:
            txt = c.get_text(strip=True).rstrip(':')
            head, _, meta = txt.partition(' · ')
            if head.startswith('THE POLL'):
                lines = []; j = i+1
                while j < len(kids) and kids[j].get('class')==['in'] and not kids[j].find('table'):
                    lines.append(inner(kids[j].find('p'))); j += 1
                blocks.append({'t':'poll','lines':lines}); i = j; continue
            if head.startswith('SOURCES'):
                links = []
                for a in kids[i+1].select('a'):
                    t = a.get_text(strip=True); outlet, sep, ttl = t.partition(' · ')
                    links.append({'outlet': outlet if sep else '', 'title': ttl if sep else t, 'url': a['href']})
                blocks.append({'t':'sources','links':links}); i += 2; continue
            blocks.append({'t':'section','head':head,'meta':meta})
        elif 'in' in cls and c.find('table'):
            rows = [split_br(inner(td)) for td in c.select('td')]
            if rows and rows[0][0] in ('TODAY','YESTERDAY','LAST','NEXT','TONIGHT'):
                out = []
                for r in rows:
                    nm, ven = name_venue(r[1]); out.append({'label':r[0],'name':nm,'venue':ven,'line':r[2] if len(r)>2 else ''})
                blocks.append({'t':'scoreboard','rows':out})
            else:
                out = []
                for r in rows:
                    nm, ven = name_venue(r[0]); out.append({'name':nm,'venue':ven,'line2':r[1] if len(r)>1 else '','line3':r[2] if len(r)>2 else ''})
                blocks.append({'t':'fixtures','rows':out})
        elif 'in' in cls:
            h = inner(c.find('p')); txt = c.get_text(' ', strip=True)
            if txt.startswith('Kickoff times'): blocks.append({'t':'note','html':h})
            elif txt.startswith('Reply'): blocks.append({'t':'ask','html':h})
            elif txt.startswith('Fan-made'): pass
            elif txt.startswith('NEXT EDITION'): blocks.append({'t':'next','text':txt.partition(':')[2].strip()})
            elif txt.startswith('FOLLOW'): blocks.append({'t':'follow','links':[{'label':a.get_text(strip=True),'url':a['href']} for a in c.select('a')]})
            else: blocks.append({'t':'p','html':h})
        i += 1
    return {'n':n,'date':date,'title':html.unescape(title),'description':html.unescape(desc),'mast_alt':html.unescape(alt),'blocks':blocks}

if __name__ == '__main__':
    for p in sys.argv[1:]:
        d = extract(p); out = f"data/edition-{d['n']}.json"
        json.dump(d, open(out,'w',encoding='utf-8'), ensure_ascii=False, indent=1)
        print(out, len(d['blocks']), 'blocks:', ' '.join(b['t'] for b in d['blocks']))
