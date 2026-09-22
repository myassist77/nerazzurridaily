#!/usr/bin/env python3
"""Give the legacy edition pages (No. 1-9, static HTML, no data/*.json) the same signup pieces
the renderer puts on every JSON edition: the Brevo form under the dek, the closing CTA band,
the phone sticky bar, the "Subscribe" top-bar link and the social/Twitter meta.

  python3 tools/nd_legacy_forms.py            # every p/edition-N/ without data/edition-N.json
Idempotent: the form step skips a page that carries id="sib-form", the nav step one that carries class="pn". Run from the repo root.
"""
import glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
import nd_render as R

def inject(path):
    s = open(path, encoding='utf-8').read()
    if 'id="sib-form"' in s:
        return 'already'
    n = int(re.search(r'edition-(\d+)/', path).group(1))
    # head: Brevo css + form css + twitter card (og tags already there)
    s = s.replace('<style>', R.SIB_CSS + '\n<style>', 1)
    s = s.replace('</style>', R.FORM_CSS + '</style>', 1)
    if 'twitter:card' not in s:   # legacy heads are BeautifulSoup-serialised: content= comes before property=
        def attr(prop):
            m = re.search(r'<meta content="([^"]*)" property="%s"/?>' % prop, s) or re.search(r'<meta property="%s" content="([^"]*)"/?>' % prop, s)
            return m.group(1) if m else ''
        tw = (f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{attr("og:title")}">'
              f'<meta name="twitter:description" content="{attr("og:description")}"><meta name="twitter:image" content="{attr("og:image")}">\n')
        s = s.replace('<link href="https://fonts.googleapis.com" rel="preconnect"', tw + '<link href="https://fonts.googleapis.com" rel="preconnect"', 1)
        assert 'twitter:card' in s, path
    # top bar: All editions -> Subscribe (the archive link stays in the footer)
    s = re.sub(r'(<span class="util">Edition No\. \d+ · [^<]*)<a href="/">All editions</a>', r'\1<a href="#subscribe">Subscribe</a>', s, count=1)
    # form under the dek
    form = R.form_block(kick='Tomorrow’s edition, 6 AM Eastern.', sub='Confirmed news kept apart from rumor. One email. Free.', extra_class='inline')
    m = re.search(r'<div class="dek">.*?</div>', s, flags=re.S)
    if not m:
        return 'NO DEK'
    s = s[:m.end()] + form + s[m.end():]
    # CTA band before Sources
    assert s.count('<div class="sources">') == 1, path
    s = s.replace('<div class="sources">', R.cta_band() + '<div class="sources">', 1)
    # footer subscribe link -> the on-page form
    s = s.replace('<a href="/subscribe/">Subscribe</a>', '<a href="#subscribe">Subscribe</a>', 1)
    # sticky bar + scripts
    assert s.rstrip().endswith('</body></html>'), path
    s = s.rstrip()[:-len('</body></html>')] + '\n' + R.STICK + R.HOME_FORM_JS + '\n</body></html>\n'
    R.require_signup_form(s, path); R.require_beacon(s, path)
    open(path, 'w', encoding='utf-8').write(s)
    return 'done'

def inject_nav(path):
    """Second, separately idempotent step: prev/next links, the byline, and the CSS/JS they need."""
    s = open(path, encoding='utf-8').read()
    if 'class="pn"' in s:
        return 'already'
    n = int(re.search(r'edition-(\d+)/', path).group(1))
    if '.pn{' not in s:   # pages injected before Phase 2 carry the older FORM_CSS
        s = s.replace('</style>', R.FORM_CSS + '</style>', 1)
    s = re.sub(r'(<p class="ask">.*?</p>)', lambda m: m.group(1) + f'<p class="byline">{R.esc(R.BYLINE)}</p>', s, count=1, flags=re.S)
    assert s.count('<div class="ctaband">') == 1, path
    s = s.replace('<div class="ctaband">', R.prev_next(n) + '<div class="ctaband">', 1)
    s = s.rstrip()[:-len('</body></html>')] + R.PN_JS + '\n</body></html>\n'
    R.require_signup_form(s, path); R.require_beacon(s, path)
    open(path, 'w', encoding='utf-8').write(s)
    return 'done'

if __name__ == '__main__':
    done = 0
    for p in sorted(glob.glob('p/edition-*/index.html'), key=lambda x: int(re.search(r'edition-(\d+)', x).group(1))):
        n = int(re.search(r'edition-(\d+)', p).group(1))
        if os.path.exists(f'data/edition-{n}.json'):
            continue
        r = inject(p); r2 = inject_nav(p); print(f'{p}: form {r}, nav {r2}'); done += 'done' in (r, r2)
    print(f'{done} legacy pages updated')
