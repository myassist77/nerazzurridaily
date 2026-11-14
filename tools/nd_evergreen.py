#!/usr/bin/env python3
"""Evergreen search pages for Nerazzurri Daily (added Nov 14, 2026).

Why: Search Console showed 525 impressions and 6 clicks in 28 days, with "inter milan news" at position 48. The
73 edition pages each chase one morning's headline; the only page that answers a question people ask every week
is /fixtures/, and it earns search traffic nobody promotes. This module adds the same kind of page three more
times and gives /fixtures/ the structure a search engine can read:

  /fixtures/                              same page as before + SportsEvent JSON-LD, real h2 headings, a per-match
                                          anchor on every row and a "where to watch in the US" line
  /results/                               every result the editions have carried, with scorers and the form line
  /injuries/                              every edition item about an injury, confirmed kept apart from reported
  /how-to-watch-inter-milan-in-the-usa/   the US broadcaster for every Inter match, taken from the daily listings

Rules baked in:
  * Nothing here is written by hand or from memory. Every fact on these pages is read from data/edition-*.json, so
    a page can only say what an edition already said, and it says which edition.
  * No page claims more than the data holds: /injuries/ is a dated log, not a list of who is fit today, and
    /results/ carries no league table because no edition stores one.
  * This layer may never break the morning build. nd_render.py calls it inside try/except and keeps its own
    /fixtures/ page when anything here fails; every page here is checked by nd_render's own require_beacon and
    require_signup_form before it is written, and a page that fails is skipped, not half-written.

Called from nd_render.build_index():   nd_evergreen.render_fixtures(R, count, first_iso) and nd_evergreen.build_pages(R, count, first_iso)
Standalone (from the repo root):       python3 tools/nd_evergreen.py      -> rewrites the four pages
"""
import datetime, glob, json, os, re

WATCH = 'how-to-watch-inter-milan-in-the-usa'
PATHS = ['results', 'injuries', WATCH]
MON = {'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6, 'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12}
MONTH3 = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
DAY3 = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
CHANNELS = {'PARAMOUNT+': 'Paramount+', 'CBS SPORTS GOLAZO': 'CBS Sports Golazo', 'CBSSN': 'CBS Sports Network',
            'UNIVERSO': 'Universo', 'PEACOCK PREMIUM': 'Peacock Premium', 'PEACOCK': 'Peacock', 'VIX': 'ViX', 'CBS': 'CBS'}
COMPS = {'SERIE A': 'Serie A', 'CHAMPIONS LEAGUE': 'Champions League', 'COPPA ITALIA': 'Coppa Italia', 'FRIENDLY': 'Friendly',
         'SUPERCOPPA ITALIANA': 'Supercoppa Italiana', 'SERIE A WOMEN': 'Serie A Women', "WOMEN'S CHAMPIONS LEAGUE": "Women's Champions League"}
SAN_SIRO = {'@type': 'StadiumOrArena', 'name': 'Stadio Giuseppe Meazza (San Siro)',
            'address': {'@type': 'PostalAddress', 'addressLocality': 'Milan', 'addressCountry': 'IT'}}
# An edition item is injury news when its headline uses one of these words, or its text uses two different ones.
INJ = re.compile(r"\b(injur\w*|hurt|sidelined|out for|muscle|muscular|strain\w*|sprain\w*|tear|torn|hamstring|thigh|calf|knee|ankle|"
                 r"adductors?|surgery|ligament|fracture\w*|lesione|affaticamento)\b", re.I)
FOOT_LINKS = ('<a href="/fixtures/">Fixtures</a> &middot; <a href="/results/">Results</a> &middot; <a href="/injuries/">Injuries</a> &middot; '
              f'<a href="/{WATCH}/">Watch in the US</a>')
EV_CSS = """
.sec .sh{display:contents;margin:0;font:inherit}
.ev-p{font-size:17px;line-height:1.6;margin:0 28px 12px;color:#3D465C}
.ev-meta{font-family:'Fragment Mono',monospace;font-size:.82rem;color:#5A647E;letter-spacing:.02em;margin:12px 0 0}
.ev-item h3{margin-top:4px}
.ev-item .go{font-family:'Fragment Mono',monospace;font-size:.84rem}
.ev-lbl{display:inline-block;font-family:'Fragment Mono',monospace;font-size:.82rem;letter-spacing:.08em;color:#fff;background:#2B5BB8;padding:2px 6px 1px;border-radius:3px;margin-right:8px}
.ev-lbl.r{background:#8C4034}
.ev-faq h3{font-family:Oswald,sans-serif;font-size:19px;line-height:1.25;color:#0B1020;margin:18px 28px 4px}
.ev-more{margin-top:14px}
@media(max-width:520px){.ev-p,.ev-faq h3{margin-left:16px;margin-right:16px}}
"""


# ------------------------------------------------------------------ reading the editions
def _clean(s):
    return (s or '').replace('\xa0', ' ').replace('&nbsp;', ' ').strip()

def _norm(s):
    return re.sub(r'\s+', ' ', re.sub('[‐-―−-]', '-', _clean(s))).lower()

def editions():
    eds = []
    for p in glob.glob('data/edition-*.json'):
        try:
            d = json.load(open(p, encoding='utf-8'))
            if isinstance(d.get('n'), int) and d.get('date') and isinstance(d.get('blocks'), list): eds.append(d)
        except Exception:
            pass
    return sorted(eds, key=lambda d: d['n'])

def channel(name):
    return CHANNELS.get(_clean(name).upper(), _clean(name).title())

def comp_name(c):
    return COMPS.get(_clean(c).upper(), _clean(c).title())

def _the(name):
    return name if name.startswith('Serie A') else 'the ' + name

def parse_row(r, ref_iso):
    """One fixtures row -> a dict. 'date' and 'et' stay None when the row's text does not parse; nothing is guessed."""
    l2 = [x.strip() for x in _clean(r.get('line2')).split('·')]
    l3 = [x.strip() for x in _clean(r.get('line3')).split('·')]
    women = 'WOMEN' in _clean(r.get('line2')).upper() or _clean(r.get('name')).upper().endswith('WOMEN')
    comp = l2[1] if len(l2) > 1 else ''
    if comp.upper() == 'INTER WOMEN' and len(l2) > 2: comp = l2[2]
    out = {'name': _clean(r.get('name')), 'venue': r.get('venue'), 'line2': r.get('line2') or '', 'line3': r.get('line3') or '',
           'comp': comp.upper(), 'date': None, 'et': None, 'et_text': '', 'cet': '', 'tv': [], 'tv_pending': False, 'women': women}
    m = re.match(r'^[A-Z]{3,9},?\s+([A-Z]{3})[A-Z]*\.?\s+(\d{1,2})$', l2[0].upper()) if l2 and l2[0] else None
    if m and m.group(1) in MON:
        ref = datetime.date.fromisoformat(ref_iso); best = None
        for y in (ref.year - 1, ref.year, ref.year + 1):
            try: d = datetime.date(y, MON[m.group(1)], int(m.group(2)))
            except ValueError: continue
            if best is None or abs((d - ref).days) < abs((best - ref).days): best = d
        out['date'] = best
    tv_on = False
    for part in l3:
        u = part.upper()
        mt = re.match(r'^(\d{1,2}):(\d{2})\s*([AP])M\s*ET$', u)
        if mt:
            out['et'] = (int(mt.group(1)) % 12 + (12 if mt.group(3) == 'P' else 0), int(mt.group(2))); out['et_text'] = part; continue
        if re.match(r'^\d{1,2}:\d{2}\s*CES?T$', u):
            out['cet'] = part; continue
        if re.match(r'^US\s*TV\s*:', u):
            tv_on = True; part = part.split(':', 1)[1].strip(); u = part.upper()
        if tv_on and part:
            if 'NOT YET' in u or u in ('TBD', 'TBC', 'NONE'): out['tv_pending'] = True
            else: out['tv'].append(channel(part))
    return out

def fixture_rows(d):
    fx = next((b for b in d['blocks'] if b.get('t') == 'fixtures'), None)
    return [parse_row(r, d['date']) for r in (fx.get('rows') or [])] if fx else []

def match_log(eds):
    """Every dated match the editions have listed, keyed by (date, women). The newest edition that carried a match wins,
    so a listing that changed late is shown as it stood on the last morning it was printed."""
    log = {}
    for d in eds:
        for r in fixture_rows(d):
            if r['date']:
                r['n'] = d['n']; log[(r['date'], r['women'])] = r
    return log

def results(eds):
    """Every 'LATEST RESULT' item, once. A result is printed for several mornings; the first printing that carries
    a form line is kept, with the number and date of the edition it comes from."""
    seen = {}; order = []
    for d in eds:
        bl = d['blocks']
        for i, b in enumerate(bl):
            if b.get('t') == 'section' and 'RESULT' in _clean(b.get('head')).upper():
                j = i + 1
                while j < len(bl) and bl[j].get('t') == 'item':
                    it = bl[j]; key = _norm(it.get('h3'))
                    rec = {'h3': it.get('h3') or '', 'paras': it.get('paras') or [], 'kicker': it.get('kicker') or '',
                           'meta': b.get('meta') or '', 'n': d['n'], 'date': d['date']}
                    if key not in seen:
                        seen[key] = rec; order.append(key)
                    elif not seen[key]['kicker'] and rec['kicker']:
                        rec['n_first'] = seen[key]['n']; seen[key] = rec
                    j += 1
    return [seen[k] for k in reversed(order)]

def score(h3):
    """'Inter 2-0 Como' -> ('W', comp-less). Returns W, D or L for Inter's men, or None when the line is not that."""
    t = _norm(re.sub(r'<[^>]+>', '', h3))
    m = re.match(r'^(.+?) (\d+)-(\d+) (.+)$', t)
    if not m or 'women' in t: return None
    home, a, b, away = m.group(1).strip(), int(m.group(2)), int(m.group(3)), m.group(4).strip()
    if home == 'inter': mine, theirs = a, b
    elif away == 'inter': mine, theirs = b, a
    else: return None
    return 'W' if mine > theirs else ('D' if mine == theirs else 'L')

def injury_items(eds, cap=40):
    out = []
    for d in reversed(eds):
        for b in d['blocks']:
            if b.get('t') != 'item': continue
            h3 = re.sub(r'<[^>]+>', '', b.get('h3') or ''); body = re.sub(r'<[^>]+>', '', ' '.join(b.get('paras') or []))
            if re.match(r'^.+ \d+\s*[‐-―−-]\s*\d+ .+$', _clean(h3)): continue          # a result line, not news
            words = {w.lower() for w in INJ.findall(body)}
            if INJ.search(h3) or len(words) >= 2:
                out.append({'h3': b.get('h3') or '', 'para': (b.get('paras') or [''])[0], 'kicker': b.get('kicker') or '',
                            'rep': bool(b.get('rep')), 'n': d['n'], 'date': d['date']})
        if len(out) >= cap: break
    return out[:cap]


# ------------------------------------------------------------------ shared markup
def _ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace('</', '<\\/') + '</script>\n'

def _sec(R, head, meta=None):
    return f'<div class="sec"><h2 class="sh"><b>{R.esc(head)}</b></h2>' + (f'<em>{R.esc(meta)}</em>' if meta else '') + '</div>'

def _day(d):
    return f'{DAY3[d.weekday()]}, {MONTH3[d.month - 1]} {d.day}'

def _slug(r):
    return re.sub(r'[^a-z0-9]+', '-', f"{r['name']} {MONTH3[r['date'].month - 1]} {r['date'].day}".lower()).strip('-') if r['date'] else ''

def _row(R, r, anchor=False):
    aid = f' id="{_slug(r)}"' if anchor and r['date'] else ''
    return (f'<tr{aid}><td><div class="nm">{R.chip(r["name"], r.get("venue"))}</div><div class="meta">{R.nbsp(r["line2"])}</div>'
            f'<div class="tm">{R.et_bold(R.nbsp(r["line3"]))}</div></td></tr>')

def _foot():
    return ('<div class="foot">Fan-made. Not affiliated with FC Internazionale Milano.<br>\n<a href="#subscribe">Subscribe</a> &middot; '
            f'<a href="/">All editions</a> &middot; {FOOT_LINKS} &middot; <a href="https://www.youtube.com/@nerazzurridaily" rel="noopener">YouTube</a> &middot; '
            '<a href="https://www.tiktok.com/@nerazzurridaily" rel="noopener">TikTok</a></div>\n')

def _more(skip):
    links = [('fixtures', 'Every kickoff in Eastern time'), ('results', 'Every result this season'), ('injuries', 'The injury log'),
             (WATCH, 'How to watch in the US')]
    return ('<p class="fx-note ev-more">' + ' &middot; '.join(f'<a href="/{p}/">{t}</a>' for p, t in links if p != skip) + '</p>')

def _head(R, here, count):
    """The page header: nd_render's masthead block when it has one, else the plain top bar and the nav strip."""
    if hasattr(R, 'masthead'): return R.masthead(here)
    return (f'<div class="top"><a class="wm" href="/">NERAZZURRI <b>DAILY</b></a><span class="util">{count} editions · <a href="#subscribe">Subscribe</a></span></div>\n'
            + (R.nav(here) if hasattr(R, 'nav') else ''))

def _checked(R, page, where):
    """nd_render's own two hard stops, turned into an exception so one bad page is skipped instead of ending the build."""
    try:
        return R.require_signup_form(R.require_beacon(page, where), where)
    except SystemExit as e:
        raise ValueError(str(e))

def _page(R, path, title, desc, h1, lede, first, rest, count, form_head, form_fine, lds):
    url = f'{R.SITE}/{path}/'
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<title>{R.esc(title)} — Nerazzurri Daily</title>'
            + R.meta(title, desc, url, R.OG_BRAND) + ''.join(_ld(x) for x in lds)
            + f'{R.FONTS}\n{R.SIB_CSS}\n<style>{R.CSS}{R.FORM_CSS}{R.FIX_CSS}{EV_CSS}</style></head><body><div class="sheet">\n'
            + _head(R, f'/{path}/', count) +
            f'<div class="hero"><h1>{R.esc(h1)}</h1><p>{lede}</p></div>\n'
            + first + R.form_block(head=form_head, fine=form_fine) + rest + _more(path)
            + R.cta_band().replace('class="ctaband"', 'class="ctaband end"') + _foot()
            + '</div>\n' + R.STICK + R.HOME_FORM_JS + '\n</body></html>\n')
    return _checked(R, page, f'{path}/index.html')

def _webpage(R, path, title, desc, iso):
    return {'@context': 'https://schema.org', '@type': 'WebPage', 'name': title, 'description': desc, 'url': f'{R.SITE}/{path}/',
            'inLanguage': 'en-US', 'dateModified': f'{iso}T05:30:00{R.et_offset(iso)}',
            'isPartOf': {'@type': 'WebSite', 'name': 'Nerazzurri Daily', 'url': R.SITE + '/'}}

def _event(R, r):
    """schema.org SportsEvent for one upcoming row, or None when the date or the Eastern kickoff did not parse."""
    if not (r['date'] and r['et'] and r['name']): return None
    iso = r['date'].isoformat(); inter = 'Inter Women' if r['women'] else 'Inter'
    home, away = (inter, r['name']) if r.get('venue') == 'HOME' else (r['name'], inter)
    ev = {'@type': 'SportsEvent', 'name': f'{home} vs {away}', 'sport': 'Soccer',
          'startDate': f"{iso}T{r['et'][0]:02d}:{r['et'][1]:02d}:00{R.et_offset(iso)}",
          'eventStatus': 'https://schema.org/EventScheduled', 'url': f'{R.SITE}/fixtures/#{_slug(r)}',
          'description': ' · '.join(x for x in (_clean(r['line2']), _clean(r['line3'])) if x),
          'homeTeam': {'@type': 'SportsTeam', 'name': home}, 'awayTeam': {'@type': 'SportsTeam', 'name': away}}
    if r.get('venue') == 'HOME' and not r['women'] and r['comp'] in ('SERIE A', 'CHAMPIONS LEAGUE', 'COPPA ITALIA'):
        ev['location'] = SAN_SIRO
    return ev

def _tv_line(rows):
    """One sentence on the US listings of the given rows, built only from what the rows say."""
    rows = [r for r in rows if not r['women']]
    if not rows: return ''
    listed = [r for r in rows if r['tv']]; pending = [r for r in rows if not r['tv']]
    chans = []
    for r in listed:
        for c in r['tv']:
            if c not in chans: chans.append(c)
    s = ''
    if listed:
        s = (f'{len(listed)} of the {len(rows)} matches above ' if len(rows) > 1 else 'The match above ') + ('have' if len(listed) != 1 else 'has') + ' a US listing: ' + ', '.join(chans) + '.'
    if pending:
        s += (' ' if s else '') + (f'{len(pending)} ' + ('have' if len(pending) != 1 else 'has') + ' none published yet; the line updates the morning one is.')
    return s


# ------------------------------------------------------------------ /fixtures/ (nd_render's page + structure a search engine can read)
def render_fixtures(R, count, first_iso):
    eds = editions(); latest = eds[-1] if eds else {'blocks': [], 'n': 0, 'date': first_iso}
    rows = fixture_rows(latest)
    note = next((b['html'] for b in latest['blocks'] if b.get('t') == 'note'), '')
    season = json.load(open('data/season-2026-27.json', encoding='utf-8'))
    title = 'Inter fixtures in Eastern time, with US TV'
    desc = ('Every upcoming Inter Milan match with the Eastern kickoff, the Milan time and the US broadcaster, plus all 38 Serie A dates of 2026-27. '
            'Updated every morning by Nerazzurri Daily.')
    events = [e for e in (_event(R, r) for r in rows) if e]
    lds = [_webpage(R, 'fixtures', title, desc, latest['date'])]
    if events:
        lds.append({'@context': 'https://schema.org', '@type': 'ItemList', 'name': 'Upcoming Inter Milan matches',
                    'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'item': e} for i, e in enumerate(events)]})
    big = {'Milan', 'Juventus', 'Napoli'}
    srows = ''.join(f'<tr><td class="md">{r["md"]:02d}</td><td class="dt">{R.esc(r["dates"])}</td><td class="op">{R.esc(r["opponent"])}{"<i></i>" if r["opponent"] in big else ""}</td>'
                    f'<td class="ha"><span class="chip">{r["venue"]}</span></td></tr>' for r in season['rows'])
    tv = _tv_line(rows)
    page = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<title>{title} — Nerazzurri Daily</title>'
            + R.meta(title, desc, f'{R.SITE}/fixtures/', R.OG_BRAND) + ''.join(_ld(x) for x in lds)
            + f'{R.FONTS}\n{R.SIB_CSS}\n<style>{R.CSS}{R.FORM_CSS}{R.FIX_CSS}{EV_CSS}</style></head><body><div class="sheet">\n'
            + _head(R, '/fixtures/', count) +
            f'<div class="hero"><h1>Inter fixtures in Eastern time.</h1><p>Every kickoff in ET first, Milan time second, and the US broadcaster once it is published. '
            f'Kept current every morning from <a href="/p/edition-{latest.get("n", "")}/">the latest edition</a>.</p></div>\n'
            + R.form_block(head='Every kickoff in your inbox', fine='Free · one email a morning with the next match at the top · unsubscribe any time')
            + _sec(R, 'Next up', 'EASTERN TIME FIRST, MILAN SECOND') + f'<div class="in"><table class="sb"><tbody>{"".join(_row(R, r, True) for r in rows)}</tbody></table></div>'
            + (f'<p class="fx-note">{note}</p>' if note else '')
            + (_sec(R, 'Where to watch in the US', 'FROM THE LISTINGS ABOVE') + f'<p class="fx-note">{R.esc(tv)} <a href="/{WATCH}/">How to watch Inter in the USA, match by match →</a></p>' if tv else '')
            + _sec(R, 'Serie A 2026-27 · all 38', 'WEEKEND WINDOWS FROM INTER.IT')
            + f'<table class="season"><tbody>{srows}</tbody></table>'
            f'<p class="fx-note">Dates are the league’s weekend windows ({R.esc(season["source"])}); the exact day and the Eastern kickoff appear above once Serie A sets them. '
            f'The pink dot marks the derby, Juventus and Napoli. HOME is San Siro.</p>'
            + _more('fixtures')
            + R.cta_band().replace('class="ctaband"', 'class="ctaband end"') + _foot()
            + '</div>\n' + R.STICK + R.HOME_FORM_JS + '\n</body></html>\n')
    return _checked(R, page, 'fixtures/index.html')


# ------------------------------------------------------------------ /results/
def render_results(R, count, first_iso):
    eds = editions(); res = results(eds)
    if not res: raise ValueError('no result has been printed in any edition yet')
    latest = eds[-1]; since = R.longdate(eds[0]['date']).split(', ', 1)[1]
    title = 'Inter Milan results 2026-27: every score and scorer'
    desc = (f'Every Inter Milan result since {since}, newest first: the score, the scorers with their minutes, the competition and matchday, '
            'and the form line from the morning after. Updated by Nerazzurri Daily.')
    tally = {}
    for r in res:
        o = score(r['h3']); c = _clean(r['meta']).split('·')[0].strip().upper()
        if o and c and c != 'FRIENDLY': tally.setdefault(c, {'W': 0, 'D': 0, 'L': 0})[o] += 1
    rec = ' · '.join(f'{comp_name(c)} {t["W"]}W {t["D"]}D {t["L"]}L' for c, t in tally.items())
    new = res[0]
    first = (_sec(R, 'Latest result', _clean(new['meta']))
             + f'<div class="item ev-item"><div class="in"><h3>{new["h3"]}</h3>' + ''.join(f'<p>{p}</p>' for p in new['paras'])
             + (f'<p class="kick">{new["kicker"]}</p>' if new['kicker'] else '')
             + f'<p class="go"><a href="/p/edition-{new["n"]}/">Read the edition that carried it, No. {new["n"]} · {R.shortdate(new["date"])} →</a></p></div></div>')
    items = ''
    for r in res[1:]:
        items += (f'<div class="item ev-item"><div class="in"><p class="ev-meta">{R.esc(_clean(r["meta"]))}</p><h3>{r["h3"]}</h3>' + ''.join(f'<p>{p}</p>' for p in r['paras'])
                  + (f'<p class="kick">{r["kicker"]}</p>' if r['kicker'] else '')
                  + f'<p class="go"><a href="/p/edition-{r["n"]}/">No. {r["n"]} · {R.shortdate(r["date"])} →</a></p></div></div>')
    rest = ((_sec(R, 'The record on this page', f'SINCE {since.upper()}') + f'<p class="ev-p">{R.esc(rec)}. That counts only the {len(res)} results below, '
             f'which start with the edition of {since}; matches played before it are not here. The form line under each result is the one printed that morning.</p>' if rec else '')
            + (_sec(R, 'Earlier results', 'NEWEST FIRST') + items if items else '')
            + '<p class="fx-note">Scores, scorers and minutes are the club’s own match reports, as printed in the edition linked under each result. '
              'This page holds no league table: the editions do not store one, so it is not shown here.</p>')
    lede = (f'Every result since {since}, newest first, with the scorers, the competition and the form line from the morning after. '
            f'Built from the editions, last updated {R.longdate(latest["date"])}.')
    return _page(R, 'results', title, desc, 'Inter Milan results, 2026-27.', lede, first, rest, count,
                 'The result, in your inbox by 6 AM', 'Free · one email a morning with the score and the scorers · unsubscribe any time',
                 [_webpage(R, 'results', title, desc, latest['date'])])


# ------------------------------------------------------------------ /injuries/
def render_injuries(R, count, first_iso):
    eds = editions(); items = injury_items(eds)
    if not items: raise ValueError('no injury item found in the editions')
    latest = eds[-1]
    title = 'Inter Milan injury news: confirmed and reported'
    desc = ('A running log of Inter Milan injury news in English: what the club has confirmed, kept apart from what the Italian papers '
            'are only reporting, each with its source and date. Updated every morning by Nerazzurri Daily.')
    def block(it):
        lbl = '<span class="ev-lbl r">REPORTED</span>' if it['rep'] else '<span class="ev-lbl">CONFIRMED</span>'
        return (f'<div class="item ev-item{" rep" if it["rep"] else ""}"><div class="in"><p class="ev-meta">{lbl}{R.esc(R.shortdate(it["date"]).upper())} · NO. {it["n"]}</p>'
                f'<h3>{it["h3"]}</h3><p>{it["para"]}</p>' + (f'<p class="kick">{it["kicker"]}</p>' if it['kicker'] else '')
                + f'<p class="go"><a href="/p/edition-{it["n"]}/">Read it in full →</a></p></div></div>')
    first = _sec(R, 'Latest', R.shortdate(items[0]['date']).upper()) + block(items[0])
    rest = ((_sec(R, 'Earlier', 'NEWEST FIRST') + ''.join(block(it) for it in items[1:]) if len(items) > 1 else '')
            + '<p class="fx-note">How to read this page: it is a dated log, not a medical bulletin. Each item shows what was said on its date, '
              'and a later item can overtake an earlier one. Blue items are things the club, a national team or a coach said on the record; '
              'pink items are press reports that had not been confirmed that morning. Items are picked automatically from the editions by their wording, '
              'so the page can miss one or include a near miss.</p>')
    lede = (f'What the club has confirmed and what the papers are only reporting about Inter injuries, newest first. '
            f'{len(items)} items from the editions, last updated {R.longdate(latest["date"])}.')
    return _page(R, 'injuries', title, desc, 'Inter Milan injury news.', lede, first, rest, count,
                 'Injury news, sorted, every morning', 'Free · one email a morning, confirmed kept apart from reported · unsubscribe any time',
                 [_webpage(R, 'injuries', title, desc, latest['date'])])


# ------------------------------------------------------------------ /how-to-watch-inter-milan-in-the-usa/
def render_watch(R, count, first_iso):
    eds = editions()
    if not eds: raise ValueError('no editions')
    latest = eds[-1]; today = datetime.date.fromisoformat(latest['date'])
    log = match_log(eds)
    upcoming = [r for r in fixture_rows(latest) if not r['women']]
    past = sorted((r for (d, w), r in log.items() if d < today and not w), key=lambda r: r['date'], reverse=True)
    if not upcoming and not past: raise ValueError('no fixture rows to build the page from')
    title = 'How to watch Inter Milan in the USA: TV and streaming, match by match'
    desc = ('Which US channel or streaming service has each Inter Milan match, with the kickoff in Eastern time: Serie A, Champions League and Coppa Italia. '
            'Taken from the listings in each morning’s edition of Nerazzurri Daily.')
    # by competition, from every men's match the editions have listed this season
    comps = {}
    for r in list(log.values()):
        if r['women'] or not r['comp'] or r['comp'] == 'FRIENDLY': continue
        c = comps.setdefault(r['comp'], {'listed': 0, 'chans': {}, 'pending': 0})
        if r['tv']:
            c['listed'] += 1
            for ch in r['tv']: c['chans'][ch] = c['chans'].get(ch, 0) + 1
        elif r['date'] >= today: c['pending'] += 1
    def comp_sentence(key):
        c = comps[key]; name = comp_name(key)
        if not c['listed']:
            return f'{name}: no US listing has been published for an Inter match yet.'
        ranked = sorted(c['chans'].items(), key=lambda kv: -kv[1]); top, k = ranked[0]
        s = (f'{name}: {top} is on the listing for ' + ('every one' if k == c['listed'] else f'{k}') + f' of the {c["listed"]} Inter matches with a published US listing this season.'
             if c['listed'] > 1 else f'{name}: the one Inter match with a published US listing this season was on {top}.')
        others = [f'{ch} ({n})' for ch, n in ranked[1:]]
        if others: s += ' Also listed on some dates: ' + ', '.join(others) + '.'
        if c['pending']: s += f' {c["pending"]} upcoming ' + ('matches have' if c['pending'] != 1 else 'match has') + ' no listing yet.'
        return s
    order = [k for k in ('SERIE A', 'CHAMPIONS LEAGUE', 'COPPA ITALIA') if k in comps] + [k for k in comps if k not in ('SERIE A', 'CHAMPIONS LEAGUE', 'COPPA ITALIA')]
    nxt = next((r for r in upcoming if r['date'] and r['date'] >= today), upcoming[0] if upcoming else None)
    faq = []
    main = [comp_sentence(k) for k in order if k in ('SERIE A', 'CHAMPIONS LEAGUE')]
    if main: faq.append(('What channel is Inter Milan on in the USA?', ' '.join(main) + ' The listing for each match is in the table on this page.'))
    if nxt and nxt['date'] and nxt['et_text']:
        where = 'at home to' if nxt.get('venue') == 'HOME' else 'away at'
        a = (f'Inter’s next match is {where} {nxt["name"]} on {_day(nxt["date"])} in {_the(comp_name(nxt["comp"]))}, kicking off at {_clean(nxt["et_text"])}'
             + (f' ({_clean(nxt["cet"])} in Milan)' if nxt['cet'] else '') + '. ')
        a += ('US listing: ' + ', '.join(nxt['tv']) + '.') if nxt['tv'] else 'No US listing has been published for it yet.'
        faq.append(('What time is the next Inter match in Eastern time?', a))
    if 'COPPA ITALIA' in comps:
        faq.append(('Is Inter’s Coppa Italia match shown in the United States?', comp_sentence('COPPA ITALIA')))
    faq.append(('Where can I see every Inter kickoff in Eastern time?',
                f'The fixtures page at {R.SITE}/fixtures/ lists every upcoming Inter match with the Eastern kickoff first, the Milan time second and the US broadcaster, and it is rebuilt every morning.'))
    lds = [_webpage(R, WATCH, title, desc, latest['date']),
           {'@context': 'https://schema.org', '@type': 'FAQPage',
            'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faq]}]
    first = (_sec(R, 'Next up', 'EASTERN TIME FIRST, WITH THE US LISTING')
             + f'<div class="in"><table class="sb"><tbody>{"".join(_row(R, r) for r in upcoming[:4])}</tbody></table></div>' if upcoming else '')
    note = next((b['html'] for b in latest['blocks'] if b.get('t') == 'note'), '')
    rest = (_sec(R, 'By competition', 'COUNTED FROM THE DAILY LISTINGS') + ''.join(f'<p class="ev-p">{R.esc(comp_sentence(k))}</p>' for k in order)
            + (f'<p class="fx-note">From the latest edition, <a href="/p/edition-{latest["n"]}/">No. {latest["n"]}</a>: {note}</p>' if note else '')
            + (_sec(R, 'Every match so far', 'WITH THE US LISTING PRINTED FOR IT') + f'<div class="in"><table class="sb"><tbody>{"".join(_row(R, r) for r in past)}</tbody></table></div>' if past else '')
            + _sec(R, 'Quick answers') + '<div class="ev-faq">' + ''.join(f'<h3>{R.esc(q)}</h3><p class="ev-p">{R.esc(a)}</p>' for q, a in faq) + '</div>'
            + '<p class="fx-note">Where this comes from: each row is the listing printed in Nerazzurri Daily for that match, on the last morning the match appeared in an edition. '
              'A broadcaster can move a match late, so check your provider on the day. Nothing here is a price or a subscription offer.</p>')
    lede = ('Which US channel or streaming service has each Inter match, with the kickoff in Eastern time. '
            f'Taken from the listings in each morning’s edition, last updated {R.longdate(latest["date"])}.')
    return _page(R, WATCH, title, desc, 'How to watch Inter Milan in the USA.', lede, first, rest, count,
                 'Kickoff time and US TV, every morning', 'Free · one email a morning with the next match and where to watch it · unsubscribe any time', lds)


# ------------------------------------------------------------------ entry points
RENDERERS = {'results': render_results, 'injuries': render_injuries, WATCH: render_watch}

def render_404(R):
    """404.html - the "Page not found" page, with the header, navigation, signup form and footer of the reference pages
    (Nov 14, 2026). It is not part of the morning build: `python3 tools/nd_evergreen.py --404` writes it and the
    rebuild-pages workflow runs that, so a later change to the header or the footer reaches it too. Every link is
    root-relative, because the page is served at whatever address was not found; no canonical and no indexing."""
    desc = 'Inter Milan in English, every morning: what the club confirmed, and what the Italian press only reported.'
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            '<title>Page not found — Nerazzurri Daily</title><meta name="robots" content="noindex"><link rel="icon" href="/favicon.svg" type="image/svg+xml">'
            f'<meta name="description" content="{R.esc(desc)}">\n'
            f'{R.FONTS}\n{R.SIB_CSS}\n<style>{R.CSS}{R.FORM_CSS}{R.FIX_CSS}{EV_CSS}</style></head><body><div class="sheet">\n'
            + _head(R, '', 0) +
            '<div class="hero"><h1>Page not found</h1><p>That page isn’t here. <a href="/">Every edition is on the front page</a>, newest first.</p></div>\n'
            + _more('')
            + R.form_block(head='Get it every morning', sub='Inter Milan in English, in 90 seconds: what the club has confirmed, kept apart from what the papers are only reporting.')
            + _foot() + '</div>\n' + R.STICK + R.HOME_FORM_JS + '\n</body></html>\n')
    return _checked(R, page, '404.html')

def build_pages(R, count, first_iso):
    """Write the three pages. Returns the paths that exist on disk afterwards (so the sitemap never lists a page that is not there)."""
    for path, fn in RENDERERS.items():
        try:
            page = fn(R, count, first_iso)
            os.makedirs(path, exist_ok=True)
            open(f'{path}/index.html', 'w', encoding='utf-8').write(page)
        except Exception as e:
            print(f'nd_evergreen: /{path}/ skipped — {e!r}')
    return [p for p in PATHS if os.path.exists(f'{p}/index.html')]

if __name__ == '__main__':
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import nd_render as R
    if '--404' in sys.argv:   # the error page only (the rebuild-pages workflow runs this)
        page = render_404(R); open('404.html', 'w', encoding='utf-8').write(page); print('nd_evergreen: 404.html', len(page), 'chars'); sys.exit()
    eds = editions(); first_iso = min(d['date'] for d in eds)
    n_all = len(re.findall(r'<loc>[^<]*/p/edition-\d+/</loc>', open('sitemap.xml', encoding='utf-8').read())) if os.path.exists('sitemap.xml') else len(eds)
    open('fixtures/index.html', 'w', encoding='utf-8').write(render_fixtures(R, n_all, first_iso))
    print('nd_evergreen: fixtures +', build_pages(R, n_all, first_iso))
