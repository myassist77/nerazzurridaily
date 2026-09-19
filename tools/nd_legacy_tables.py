#!/usr/bin/env python3
"""One-time, idempotent: rebuild the flattened tables in editions 1-9.

The beehiiv import flattened every multi-column table into one cell per row and
left each column header as its own one-cell table followed by a duplicate <p>.
nd_legacy_restyle.py (Sept 19) swapped the stylesheet but left those tables
alone, so the Sept-19 CSS (which expects .lbl/.nm/.tm/.meta inside .sb cells)
rendered them as bare stacked rows. This pass rebuilds:
  - the scoreboard (TODAY / LAST / NEXT) into the current three-row .sb block,
  - the NEXT UP fixtures into the current fixture rows (opponent + HOME/AWAY
    chip, date · competition, ET bold · CEST),
  - the summer arrivals/departures ledger into a two-column table (legacy only;
    the ledger was retired with edition 10, so its CSS lives in a small
    page-level <style data-legacy> block, not in nd_render.CSS).
Usage: python3 tools/nd_legacy_tables.py p/edition-1/index.html [...]
"""
import re, sys
from bs4 import BeautifulSoup

LEDGER_CSS = (".sb.ledger th{font-family:'Fragment Mono',monospace;font-size:.82rem;font-weight:400;"
              "color:#5A647E;letter-spacing:.08em;text-align:left;padding:0 0 4px;border-bottom:1px solid #D8DFEC}"
              ".sb.ledger td{width:50%;vertical-align:top;padding:9px 12px 9px 0}"
              ".sb.ledger .nm{font-size:16px}")

def lines(td):
    """Split a flattened cell on <br> into plain-text lines."""
    out, cur = [], ''
    for node in td.contents:
        if getattr(node, 'name', None) == 'br':
            out.append(cur.strip()); cur = ''
        else:
            cur += node.get_text() if hasattr(node, 'get_text') else str(node)
    out.append(cur.strip())
    return [re.sub(r'\s+', ' ', x) for x in out if x.strip()]

def is_flat_label(div):
    t = div.find('table', class_='sb') if div.name == 'div' else None
    return bool(t) and len(t.select('td')) == 1 and not t.select('.lbl,.nm,.meta')

def take_group(start):
    """From a one-cell label table, collect [(label, node...)] pairs until the content table."""
    labels, junk, node = [], [], start
    while node is not None and is_flat_label(node):
        labels.append(node.select_one('td').get_text(' ', strip=True)); junk.append(node)
        nxt = node.find_next_sibling()
        if nxt is not None and nxt.name == 'div' and 'in' in nxt.get('class', []) and nxt.find('p') and not nxt.find('table') \
           and nxt.get_text(' ', strip=True) == labels[-1]:
            junk.append(nxt); nxt = nxt.find_next_sibling()
        node = nxt
    content = node if node is not None and node.name == 'div' and node.find('table', class_='sb') else None
    return labels, junk, content

def chip_split(name):
    m = re.match(r'^(.*?)\s*[·•]\s*(home|away)$', name, re.I)
    if m: return m.group(1).strip(), m.group(2).upper()
    m = re.match(r'^(.*?)\s*\((H|A)\)$', name)
    if m: return m.group(1).strip(), 'HOME' if m.group(2) == 'H' else 'AWAY'
    return name, None

def cell(s, parts):
    td = s.new_tag('td')
    for cls, html in parts:
        if html is None: continue
        d = s.new_tag('div', attrs={'class': cls}); d.append(BeautifulSoup(html, 'html.parser')); td.append(d)
    return td

def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def nm_html(name):
    base, chip = chip_split(name)
    return esc(base) + (f'<span class="chip">{chip}</span>' if chip else '')

def rebuild(path):
    s = BeautifulSoup(open(path, encoding='utf-8').read(), 'lxml')
    sheet = s.select_one('.sheet'); changed = 0
    for div in list(sheet.find_all('div', class_='in', recursive=False)):
        if div.parent is None or not is_flat_label(div): continue   # parent None = already removed as junk
        labels, junk, content = take_group(div)
        if content is None: continue
        cells = content.select('td')
        table = s.new_tag('table', attrs={'class': 'sb'}); tb = s.new_tag('tbody'); table.append(tb)
        up = [l.upper() for l in labels]
        if len(labels) == 3 and up[0] == 'DATE · COMPETITION':          # fixtures
            for i in range(0, len(cells) - 2, 3):
                d, o, t = lines(cells[i]), lines(cells[i + 1]), lines(cells[i + 2])
                name = o[0] if o else ''; venue = o[1].upper() if len(o) > 1 else None
                nm = esc(name) + (f'<span class="chip">{venue}</span>' if venue in ('HOME', 'AWAY') else (' · ' + esc(o[1]) if len(o) > 1 else ''))
                meta = ' · '.join(esc(x) for x in d)
                tm = (f'<b>{esc(t[0])}</b>' + ''.join(' · ' + esc(x) for x in t[1:])) if t and re.search(r'\bET\b', t[0]) else ' · '.join(esc(x) for x in t)
                tr = s.new_tag('tr'); tr.append(cell(s, [('nm', nm), ('meta', meta), ('tm', tm or None)])); tb.append(tr)
        elif len(labels) == 2 and up[0].startswith('ARRIVALS'):          # summer ledger, two columns row-major
            table['class'] = ['sb', 'ledger']
            hr = s.new_tag('tr')
            for l in labels:
                th = s.new_tag('th'); th.string = l; hr.append(th)
            tb.append(hr)
            for i in range(0, len(cells) - 1, 2):
                tr = s.new_tag('tr')
                for c in (cells[i], cells[i + 1]):
                    ln = lines(c); tr.append(cell(s, [('nm', esc(ln[0]) if ln else ''), ('tm', esc(ln[1]) if len(ln) > 1 else None)]))
                tb.append(tr)
            if not s.find('style', attrs={'data-legacy': True}):
                st = s.new_tag('style', attrs={'data-legacy': '1'}); st.string = LEDGER_CSS; s.find('style').insert_after(st)
        elif len(labels) == 3 and len(cells) == 3:                        # scoreboard
            for lab, c in zip(labels, cells):
                ln = lines(c)
                tr = s.new_tag('tr'); tr.append(cell(s, [('lbl', esc(lab)), ('nm', nm_html(ln[0]) if ln else ''), ('tm', esc(ln[1]) if len(ln) > 1 else None)])); tb.append(tr)
        else:
            continue
        wrap = s.new_tag('div', attrs={'class': 'in'}); wrap.append(table)
        content.replace_with(wrap)
        for j in junk: j.decompose()
        changed += 1
    # footnotes that sat under the flattened tables as bare paragraphs -> the sign-off note style
    for div in list(sheet.find_all('div', class_='in', recursive=False)):
        if div.find('table') or not div.find('p') or div.find('h3'): continue
        if len(div.find_all(recursive=False)) != 1: continue
        p = div.find('p')
        if p.get('class'): continue
        p['class'] = ['note']
        wrap = s.new_tag('div', attrs={'class': 'signoff'}); div.replace_with(wrap); wrap.append(p); changed += 1
    if changed:
        open(path, 'w', encoding='utf-8').write(str(s))
    return changed

if __name__ == '__main__':
    for p in sys.argv[1:]:
        print(p, 'rebuilt tables:', rebuild(p))
