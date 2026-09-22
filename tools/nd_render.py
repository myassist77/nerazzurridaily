#!/usr/bin/env python3
"""Nerazzurri Daily renderer (design of Sept 19, 2026).
  python3 tools/nd_render.py data/edition-N.json           -> p/edition-N/index.html, build/email-N.html, build/edition-N.txt
  python3 tools/nd_render.py --index                        -> index.html, subscribe/index.html, fixtures/index.html, feed.xml, sitemap.xml, go/<channel>/index.html (from data/*.json + data/legacy.json + data/season-2026-27.json)
Run from the repo root. The masthead must already exist at assets/mast/edition-NN.png.
"""
import sys, os, re, json, html, glob, datetime

SITE = "https://www.nerazzurridaily.com"
MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"]
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@400;700&amp;family=Fragment+Mono&amp;display=swap" rel="stylesheet">'
BEACON = '<!-- Cloudflare Web Analytics --><script type="module" src="https://static.cloudflareinsights.com/beacon.min.js" data-cf-beacon=\'{"token": "fd1d42426a934b7e94ed7cfe7afc9ccc"}\'></script><!-- End Cloudflare Web Analytics -->'
FONTS = FONTS + "\n" + BEACON
BEACON_TOKEN = 'fd1d42426a934b7e94ed7cfe7afc9ccc'

# --- home-page signup (Brevo embed, same form/list as /subscribe/) -------------
SIB_CSS = '<link rel="stylesheet" href="https://sibforms.com/forms/end-form/build/sib-styles.css">'
SIB_ACTION = "https://5d0cb217.sibforms.com/serve/MUIFAJ3SmPYzs20wwcA8qQBVEbp0G5VvIgN2Vat37LHRlACpca9Vyye8H1UlOIx_uslSoenaIDoVoavVqumWN5ySp6nNBq-DU6eZ_b-GF4BCLnW-dfNRrsZDLlRqHHu7NkolBLbASbHXxzLaKILxN5zMN5LSboyFFKbqGquO7wy8x_VHjKdUhyRaNnAJP6Ns4V4TgN1m_EfIIkndsw=="
SIB_LOADER_SVG = (
    '<svg class="icon clickable__icon progress-indicator__icon sib-hide-loader-icon" '
    'viewBox="0 0 512 512" width="16" height="16"><path d="M460.116 373.846l-20.823-12.022c-5.541-3.199-7.54-10.159-4.663-15.874 '
    '30.137-59.886 28.343-131.652-5.386-189.946-33.641-58.394-94.896-95.833-161.827-99.676C261.028 55.961 256 50.751 256 '
    '44.352V20.309c0-6.904 5.808-12.337 12.703-11.982 83.556 4.306 160.163 50.864 202.11 123.677 42.063 72.696 44.079 '
    '162.316 6.031 236.832-3.14 6.148-10.75 8.461-16.728 5.01z"/></svg>'
)


CONFIRM_MSG = ("Almost there. Check your inbox for an email from Nerazzurri Daily and tap the confirm link. "
               "Nothing arrives until you do. Not there in a minute? Look in spam or Promotions.")

# --- house copy (one headline, one promise, everywhere — audit of Sept 22, 2026) -------------
HEADLINE = 'Inter Milan in English, every morning, in 90 seconds.'
SUBLINE = ('What the club has confirmed, what the papers are only reporting — kept apart, with the source and date on every item. '
           'Kickoffs in Eastern time first.')
BUTTON = 'Send me tomorrow’s edition'
FINE = 'Free · one email a morning · unsubscribe any time'
SOURCES_LINE = 'built from Gazzetta dello Sport, Corriere dello Sport, Sky Sport Italia and Inter.it'
OG_BRAND = f'{SITE}/assets/og/nerazzurri-daily-1200x630.png'
BYLINE = 'Written every morning by an Inter fan in New Jersey who reads the Italian press so you don\u2019t have to.'
WHO_HEAD = 'Who writes this'
WHO = ('An Inter fan in New Jersey who reads the Italian press so you don\u2019t have to. Every morning I go through Gazzetta, Corriere, '
       'Sky Sport Italia and Inter.it, keep what the club has actually said apart from what the papers are guessing, and send it before you\u2019re up. '
       'Reply to any edition \u2014 I read every one.')

FORM_CSS = """
.hero{padding:22px 28px 0}
.hero h1{font-family:Oswald,sans-serif;font-size:30px;line-height:1.12;color:#0B1020;margin:0 0 8px;text-wrap:balance}
.hero p,.hero-p{font-size:17px;line-height:1.55;margin:0}
.hero-h{font-family:Oswald,sans-serif;font-size:28px;line-height:1.12;color:#0B1020;margin:0 0 8px;text-wrap:balance}
.formbox{margin:18px 28px 8px;padding:18px 18px 14px;border:1px solid #D8DFEC;background:#fff}
.formbox .sec{margin:0 0 12px}
.formbox.inline{margin:16px 28px 0;padding:14px 18px 12px;background:#EEF1F6;border-color:#C4CDDE}
.formbox.inline .kick2{font-family:Oswald,sans-serif;font-weight:700;font-size:17px;color:#0B1020;margin:0 0 2px}
.formbox .kick3{font-size:15px;line-height:1.5;color:#3D465C;margin:0 0 10px}
.fine{font-family:'Fragment Mono',monospace;font-size:.82rem;color:#5A647E;line-height:1.6}
.proof{font-family:'Fragment Mono',monospace;font-size:.82rem;color:#5A647E;line-height:1.7;margin:10px 28px 0}
.idx h2{font-family:Oswald,sans-serif;font-size:22px;color:#0B1020;margin:26px 0 10px}
.ctaband{background:#06080F;color:#fff;margin:26px 0 0;padding:16px 28px;display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
.ctaband span{font-family:Oswald,sans-serif;font-weight:700;font-size:18px;line-height:1.25}
.ctaband a{display:inline-block;background:#2B5BB8;color:#fff;font-family:Oswald,sans-serif;font-weight:700;font-size:16px;letter-spacing:.04em;padding:10px 16px;border-radius:3px;text-decoration:none}
.ctaband a:hover{background:#234A9A}
.pn{display:flex;justify-content:space-between;gap:12px;margin:22px 28px 0;flex-wrap:wrap}
.pn a{font-family:Oswald,sans-serif;font-weight:700;font-size:15px;color:#0A2A66;text-decoration:none;line-height:1.3}
.pn a small{display:block;font-family:'Fragment Mono',monospace;font-size:.82rem;color:#5A647E;font-weight:400;letter-spacing:.04em}
.pn a.next{text-align:right;margin-left:auto}
.pn a[hidden]{display:none}
.signoff .share{font-family:'Fragment Mono',monospace;font-size:.82rem;color:#5A647E;line-height:1.6;margin:10px 0 0}
.signoff .share a{color:#0A2A66}
.signoff .byline{font-family:'Fragment Mono',monospace;font-size:.82rem;color:#5A647E;line-height:1.6;margin:14px 0 0}
.stick{display:none}
@media(max-width:700px){
  .stick{position:fixed;left:0;right:0;bottom:0;z-index:20;display:flex;align-items:center;gap:10px;background:#06080F;color:#fff;padding:10px 12px;padding-bottom:calc(10px + env(safe-area-inset-bottom,0px));box-shadow:0 -6px 18px rgba(6,8,15,.25)}
  .stick[hidden]{display:none}
  .stick span{flex:1;font-family:Oswald,sans-serif;font-weight:700;font-size:15px;line-height:1.2}
  .stick a{background:#2B5BB8;color:#fff;font-family:Oswald,sans-serif;font-weight:700;font-size:15px;padding:9px 12px;border-radius:3px;text-decoration:none;white-space:nowrap}
  .stick button{background:transparent;border:0;color:#DCE3EF;font-size:22px;line-height:1;padding:4px 6px;cursor:pointer}
  body.has-stick{padding-bottom:64px}
}
/* Brevo form, restyled to the house design (ids/classes kept: Brevo's script uses them) */
.sib-form{text-align:left;background:transparent;padding:0}
#sib-container{max-width:none;border:0;background:transparent;padding:0;text-align:left}
#sib-form .row{display:flex;gap:10px;flex-wrap:wrap;align-items:flex-start}
#sib-form .entry__field{margin:0 !important;padding:0 !important}
#sib-form input.input{flex:1 1 220px;min-width:0;height:46px;box-sizing:border-box;padding:0 12px;border:1px solid #C4CDDE;border-radius:3px;font-family:Georgia,'Times New Roman',serif;font-size:17px;color:#0B1020;background:#fff}
#sib-form input.input:focus{outline:2px solid #2B5BB8;outline-offset:1px;border-color:#2B5BB8}
#sib-form input.input::placeholder{color:#6B7590;font-family:Georgia,serif}
#sib-form .sib-form-block__button{height:46px;padding:0 20px;border:0;border-radius:3px;background:#2B5BB8;color:#fff;font-family:Oswald,sans-serif;font-weight:700;font-size:17px;letter-spacing:.04em;cursor:pointer;white-space:nowrap}
#sib-form .sib-form-block__button:hover{background:#234A9A}
#sib-form .sib-form-block__button:focus-visible{outline:2px solid #0B1020;outline-offset:2px}
.sib-form-message-panel{font-family:Georgia,serif;font-size:16px;margin:0 0 12px;max-width:none}
#error-message{color:#661d1d;background:#FBEAE7;border:1px solid #E7B4AE;border-radius:3px}
#success-message{color:#0B1020;background:#EEF1F6;border:1px solid #2B5BB8;border-radius:3px}
.entry__error{font-family:'Fragment Mono',monospace;font-size:.82rem;color:#8C4034;margin-top:6px}
.input--hidden{display:none}
@media(max-width:520px){.hero{padding-left:16px;padding-right:16px}.formbox,.formbox.inline{margin-left:16px;margin-right:16px}.proof{margin-left:16px;margin-right:16px}.ctaband{padding-left:16px;padding-right:16px}}
"""
HOME_CSS = """
.hero2{display:grid;grid-template-columns:1.1fr .9fr;gap:22px;padding:22px 28px 0;align-items:start}
.hero2 .formbox{margin:14px 0 0}
.hero2 .proof{margin:10px 0 0}
.card{display:block;text-decoration:none;color:inherit;border:1px solid #C4CDDE;box-shadow:0 10px 24px rgba(11,16,32,.14);background:#fff;margin-top:4px}
.card img{display:block;width:100%;height:auto;border:0}
.card .cb{padding:10px 12px 12px}
.card .eyebrow{font-family:'Fragment Mono',monospace;font-size:.82rem;letter-spacing:.06em;text-transform:uppercase;color:#5A647E;margin:0 0 6px}
.card .cdek{font-size:15px;line-height:1.5;margin:0 0 10px;color:#3D465C}
.card .ci{border-left:4px solid #2B5BB8;background:#EEF1F6;padding:6px 8px;margin:6px 0;font-family:Oswald,sans-serif;font-weight:700;font-size:15px;color:#0B1020;line-height:1.3}
.card .ci.rep{border-left-color:#E7B4AE;background:#FBEAE7}
.card .ci small{display:block;font-family:'Fragment Mono',monospace;font-size:.82rem;font-weight:700;letter-spacing:.08em;color:#2B5BB8;margin-bottom:2px}
.card .ci.rep small{color:#8C4034}
.card .go{display:inline-block;margin-top:10px;font-family:Oswald,sans-serif;font-weight:700;font-size:15px;color:#0A2A66}
.three{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:26px 28px 0}
.three div{border-top:3px solid #2B5BB8;background:#EEF1F6;padding:10px 12px;font-size:15px;line-height:1.5}
.three div.r{border-top-color:#E7B4AE;background:#FBEAE7}
.three b{display:block;font-family:Oswald,sans-serif;font-size:15px;letter-spacing:.06em;text-transform:uppercase;color:#0B1020;margin-bottom:2px}
.who{display:flex;gap:14px;align-items:flex-start;margin:22px 28px 0;padding:14px 16px;border:1px solid #D8DFEC}
.who .mk{flex:0 0 44px;height:44px;border-radius:50%;background:#06080F;color:#8FB2F0;font-family:Oswald,sans-serif;font-weight:700;display:flex;align-items:center;justify-content:center;font-size:15px;letter-spacing:.04em}
.who b{display:block;font-family:Oswald,sans-serif;font-size:15px;letter-spacing:.06em;text-transform:uppercase;color:#0B1020;margin-bottom:4px}
.who p{margin:0;font-size:16px;line-height:1.55}
.idx.compact li{padding:9px 0}
.idx.compact .t{font-size:1rem;margin-top:1px}
.idx.compact .d{font-size:.78rem}
.ctaband.end{margin-top:26px}
@media(max-width:600px){.hero2{grid-template-columns:1fr;gap:16px}.three{grid-template-columns:1fr}}
@media(max-width:520px){.hero2{padding-left:16px;padding-right:16px}.three,.who{margin-left:16px;margin-right:16px}}
"""
HOME_FORM_CSS = FORM_CSS   # older name, kept for callers

def form_block(head=None, kick=None, sub=None, extra_class='', fine=FINE):
    """The one Brevo form a page may carry (Brevo's main.js binds to id="sib-form", so never two per page).
    Functional markup (action, ids, loader svg, hidden fields, message panels) is fixed; only the words around it vary."""
    top = ''
    if head: top += f'<div class="sec"><b>{esc(head)}</b></div>\n'
    if kick: top += f'<p class="kick2">{esc(kick)}</p>'
    if sub: top += f'<p class="kick3">{esc(sub)}</p>'
    return (f'<div class="formbox{(" " + extra_class) if extra_class else ""}" id="subscribe">{top}'
            '<div class="sib-form"><div id="sib-form-container" class="sib-form-container">\n'
            '  <div id="error-message" class="sib-form-message-panel"><div class="sib-form-message-panel__text sib-form-message-panel__text--center"><span class="sib-form-message-panel__inner-text">That didn\'t go through. Check the address and try once more.</span></div></div>\n'
            '  <div></div>\n'
            '  <div id="success-message" class="sib-form-message-panel"><div class="sib-form-message-panel__text sib-form-message-panel__text--center"><span class="sib-form-message-panel__inner-text">' + CONFIRM_MSG + '</span></div></div>\n'
            '  <div></div>\n'
            '  <div id="sib-container" class="sib-container--large sib-container--vertical">\n'
            '    <form id="sib-form" method="POST" action="' + SIB_ACTION + '" data-type="subscription">\n'
            '      <div class="sib-input sib-form-block"><div class="form__entry entry_block"><div class="form__label-row">\n'
            '        <label class="sr" for="EMAIL">Your email</label>\n'
            '        <div class="row">\n'
            '          <div class="entry__field" style="flex:1 1 220px;display:flex"><input class="input" type="email" id="EMAIL" name="EMAIL" autocomplete="email" inputmode="email" value="" placeholder="you@example.com" data-required="true" required></div>\n'
            '          <button class="sib-form-block__button sib-form-block__button-with-loader" form="sib-form" type="submit">' + SIB_LOADER_SVG + BUTTON + '</button>\n'
            '        </div></div>\n'
            '        <label class="entry__error entry__error--primary"></label>\n'
            '      </div></div>\n'
            '      <input type="text" name="email_address_check" value="" class="input--hidden" tabindex="-1" autocomplete="off" aria-hidden="true">\n'
            '      <input type="hidden" name="locale" value="en">\n'
            '    </form>\n'
            '  </div>\n'
            '</div></div>\n'
            + (f'<p class="fine" style="margin:10px 0 0">{esc(fine)}</p>' if fine else '') + '</div>\n')

def edition_index():
    """{n: (date, title)} for every edition: data/*.json plus data/legacy.json."""
    eds = {}
    for p in glob.glob('data/edition-*.json'):
        d = json.load(open(p, encoding='utf-8')); eds[d['n']] = (d['date'], d['title'])
    if os.path.exists('data/legacy.json'):
        for e in json.load(open('data/legacy.json', encoding='utf-8')): eds.setdefault(e['n'], (e['date'], e['title']))
    return eds

def prev_next(n, eds=None):
    """Previous edition with its title (known at build time); the next one is revealed by JS once it exists,
    so yesterday's page never needs a rebuild when today's is published."""
    eds = eds if eds is not None else edition_index()
    out = '<div class="pn">'
    if n - 1 in eds:
        out += f'<a href="/p/edition-{n-1}/"><small>\u2190 Previous edition \u00b7 No. {n-1}</small>{esc(eds[n-1][1])}</a>'
    out += f'<a class="next" id="pn-next" hidden href="/p/edition-{n+1}/"><small>Next edition \u00b7 No. {n+1} \u2192</small>' + (esc(eds[n+1][1]) if n + 1 in eds else 'Read it') + '</a></div>\n'
    return out

PN_JS = """<script>(function(){var a=document.getElementById('pn-next');if(!a)return;fetch(a.getAttribute('href'),{method:'HEAD'}).then(function(r){if(r.ok)a.hidden=false;}).catch(function(){});})();</script>"""

def et_offset(iso):
    """-04:00 or -05:00 for a date in America/New_York."""
    from zoneinfo import ZoneInfo
    off = datetime.datetime.fromisoformat(iso + 'T05:30:00').replace(tzinfo=ZoneInfo('America/New_York')).utcoffset()
    h = int(off.total_seconds() // 3600); return f'{h:+03d}:00'

def jsonld_article(n, title, desc, iso, image):
    d = {"@context": "https://schema.org", "@type": "NewsArticle", "headline": title, "description": desc,
         "datePublished": f"{iso}T05:30:00{et_offset(iso)}", "dateModified": f"{iso}T05:30:00{et_offset(iso)}",
         "image": [image], "mainEntityOfPage": f"{SITE}/p/edition-{n}/", "inLanguage": "en-US",
         "author": {"@type": "Person", "name": "Nerazzurri Daily"},
         "publisher": {"@type": "Organization", "name": "Nerazzurri Daily", "url": SITE, "logo": {"@type": "ImageObject", "url": OG_BRAND}}}
    return '<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False).replace('</', '<\\/') + '</script>\n'

# --- tracking doors (Sept 22, 2026): Cloudflare Web Analytics records paths and referrers, never query strings.
# A door is a tiny page under /go/<channel>/ that carries the beacon, rewrites its own path to /go/<channel>/ed{N}/
# (history.replaceState, before the beacon loads) and then redirects to the target — so the channel AND the edition
# show up as a requestPath, and the landing page's refererPath, with no dependence on utm_* or third-party referrers.
DOORS = {'yt': '/subscribe/', 'tt': '/subscribe/', 'wa': '/', 'copy': '/', 'x': '/', 'forward': '/subscribe/', 'welcome': '/'}

def door_url(channel, n=None, to=None, variant=None):
    q = []
    if n: q.append(f'ed={n}')
    if variant: q.append(f'v={variant}')
    if to and to != DOORS[channel]: q.append('to=' + to)
    return f'{SITE}/go/{channel}/' + ('?' + '&'.join(q) if q else '')

def render_door(channel):
    default = DOORS[channel]
    desc = 'Inter Milan in English, every morning, in 90 seconds \u2014 what the club has confirmed, kept apart from what the papers are only reporting. Free.'
    pre = ('<script>(function(){var q=new URLSearchParams(location.search),to=q.get("to")||%s,ed=(q.get("ed")||"").replace(/\\D/g,""),v=(q.get("v")||"").replace(/[^a-z0-9-]/gi,"");'
           'if(!/^\\/(?!\\/)[A-Za-z0-9_\\-./?=&%%]*$/.test(to))to=%s;window.__to=to;'
           'try{history.replaceState(null,"",location.pathname+(ed?"ed"+ed+"/":"")+(v?v+"/":""));}catch(e){}})();</script>\n') % (json.dumps(default), json.dumps(default))
    page = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<title>Nerazzurri Daily</title><meta name="robots" content="noindex,nofollow">'
            + pre + meta('Nerazzurri Daily \u2014 Inter Milan in English, every morning', desc, f'{SITE}{default}', OG_BRAND)
            + f'{FONTS}\n<style>{CSS}.go{{padding:40px 28px 48px;text-align:center}}.go p{{font-size:17px;line-height:1.6;margin:0 0 14px}}.go a{{font-family:Oswald,sans-serif;font-weight:700;font-size:17px;color:#0A2A66}}</style></head>'
            f'<body><div class="sheet"><div class="top"><a class="wm" href="/">NERAZZURRI <b>DAILY</b></a></div>'
            f'<div class="go"><p>Taking you to Nerazzurri Daily\u2026</p><p><a id="go" href="{default}">Continue \u2192</a></p></div></div>\n'
            '<script>(function(){var a=document.getElementById("go"),t=window.__to||a.getAttribute("href");a.setAttribute("href",t);'
            'window.addEventListener("load",function(){setTimeout(function(){location.replace(t);},700);});})();</script>\n</body></html>\n')
    return require_beacon(page, f'go/{channel}/index.html')

def share_block(n, title):
    """Page sign-off: X, WhatsApp and copy-link, each UTM-tagged so Cloudflare shows what forwards do."""
    from urllib.parse import quote
    page = f'/p/edition-{n}/'
    text = f'{title} \u2014 Nerazzurri Daily'
    x = 'https://x.com/intent/post?text=' + quote(text) + '&url=' + quote(f'{SITE}{page}?utm_source=share&utm_medium=x&utm_campaign=ed{n}')
    wa = 'https://wa.me/?text=' + quote(text + ' ' + door_url('wa', n, page))
    return (f'<p class="share">Know an Interista? Send them this one: <a href="{x}" rel="noopener" target="_blank">X</a> \u00b7 '
            f'<a href="{wa}" rel="noopener" target="_blank">WhatsApp</a> \u00b7 <a href="{door_url("copy", n, page)}" id="copy-link">Copy link</a></p>')

SHARE_JS = """<script>(function(){var a=document.getElementById('copy-link');if(!a||!navigator.clipboard)return;a.addEventListener('click',function(e){e.preventDefault();navigator.clipboard.writeText(a.getAttribute('href')).then(function(){var t=a.textContent;a.textContent='Copied';setTimeout(function(){a.textContent=t;},1500);});});})();</script>"""

def proof_line(count, first_iso):
    d = datetime.date.fromisoformat(first_iso)
    return f'<p class="proof">{count} editions · every morning since {MONTHS[d.month-1][:3]} {d.day}, {d.year} · {SOURCES_LINE}</p>\n'

def cta_band():
    return ('<div class="ctaband"><span>Tomorrow’s edition lands at 6 AM Eastern.</span>'
            '<a href="#subscribe">Get it free →</a></div>\n')

STICK = ('<div class="stick" id="stick" hidden><span>Inter, every morning, 6 AM ET</span><a href="#subscribe">Get it free</a>'
         '<button type="button" id="stick-x" aria-label="Dismiss">×</button></div>\n')

def meta(title, desc, url, image, kind='website', published=None):
    """canonical + description + Open Graph + Twitter card (+ article:published_time for editions)."""
    m = (f'<link rel="canonical" href="{url}"><link rel="icon" href="/favicon.svg" type="image/svg+xml">'
         f'<meta name="description" content="{esc(desc)}">\n'
         f'<meta property="og:site_name" content="Nerazzurri Daily"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">\n'
         f'<meta property="og:type" content="{kind}"><meta property="og:url" content="{url}"><meta property="og:image" content="{image}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">\n'
         f'<link rel="alternate" type="application/rss+xml" title="Nerazzurri Daily" href="{SITE}/feed.xml">'
         f'<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(desc)}"><meta name="twitter:image" content="{image}">\n')
    if published: m += f'<meta property="article:published_time" content="{published}">\n'
    return m

HOME_FORM_JS = """<script>
  window.REQUIRED_CODE_ERROR_MESSAGE = 'Please choose a country code';
  window.LOCALE = 'en';
  window.EMAIL_INVALID_MESSAGE = window.SMS_INVALID_MESSAGE = "That doesn't look like an email address.";
  window.REQUIRED_ERROR_MESSAGE = "Enter your email address.";
  window.GENERIC_INVALID_MESSAGE = "That doesn't look right. Check it and try again.";
  window.INVALID_NUMBER = "That doesn't look right.";
  window.INVALID_DATE = "Please enter a valid date";
  window.REQUIRED_MULTISELECT_MESSAGE = 'Please select at least 1 option';
  window.translation = { common: { selectedList: '{quantity} list selected', selectedLists: '{quantity} lists selected', selectedOption: '{quantity} selected', selectedOptions: '{quantity} selected' } };
  var AUTOHIDE = Boolean(0);
</script>
<script defer src="https://sibforms.com/forms/end-form/build/main.js"></script>
<script>
/* Brevo's script overwrites the success text with a generic line; keep ours, which tells people to confirm. */
(function(){var M=%s;var p=document.getElementById('success-message');if(!p)return;
function fix(){var s=p.querySelector('.sib-form-message-panel__inner-text');if(s&&s.textContent!==M){s.textContent=M;}}
new MutationObserver(fix).observe(p,{childList:true,subtree:true,characterData:true});})();
/* Every "Subscribe" link on the page goes to the one form and puts the cursor in it. */
(function(){var f=document.getElementById('subscribe');if(!f)return;
document.querySelectorAll('a[href="#subscribe"]').forEach(function(a){a.addEventListener('click',function(e){e.preventDefault();
  f.scrollIntoView({behavior:'smooth',block:'center'});var i=document.getElementById('EMAIL');if(i)setTimeout(function(){i.focus({preventScroll:true});},450);});});
/* Phone-only sticky bar: hidden while the form is on screen, gone after a submit or a dismiss (remembered on this device). */
var s=document.getElementById('stick');if(!s)return;var K='nd_stick_off';var off=false;try{off=localStorage.getItem(K)==='1';}catch(e){}
if(off)return;var formOn=false;function upd(){s.hidden=formOn;document.body.classList.toggle('has-stick',!formOn);}
if('IntersectionObserver' in window){new IntersectionObserver(function(es){formOn=es[0].isIntersecting;upd();},{threshold:0.2}).observe(f);}
upd();function kill(){s.hidden=true;document.body.classList.remove('has-stick');try{localStorage.setItem(K,'1');}catch(e){}}
document.getElementById('stick-x').addEventListener('click',kill);var fm=document.getElementById('sib-form');if(fm)fm.addEventListener('submit',kill);})();
</script>""" % json.dumps(CONFIRM_MSG)

def require_signup_form(page, where):
    '''Hard stop: the home page is not written without a working signup form.'''
    if SIB_ACTION not in page or 'id="sib-form"' not in page or 'sibforms.com/forms/end-form/build/main.js' not in page:
        sys.exit(f'nd_render: REFUSING to write {where} \u2014 the Brevo signup form is missing or incomplete.')
    # Brevo's main.js calls removeClass() on this loader icon the moment the form is
    # submitted. Without it the handler throws, no POST is sent, and the form silently
    # swallows every signup (live on the home page 20 Sep 2026). Never ship the button
    # without it.
    if 'sib-hide-loader-icon' not in page:
        sys.exit(f'nd_render: REFUSING to write {where} \u2014 the Subscribe button is missing the loader icon; Brevo main.js throws on submit and no signup is sent.')
    return page


def require_beacon(page, where):
    """Hard stop: no web page is written without the Cloudflare Web Analytics beacon."""
    if 'static.cloudflareinsights.com/beacon.min.js' not in page or BEACON_TOKEN not in page:
        sys.exit(f'nd_render: REFUSING to write {where} — Cloudflare Web Analytics beacon missing')
    return page

def forbid_beacon(page, where):
    """Email must never carry the beacon (scripts are stripped by mail clients and hurt deliverability)."""
    if 'cloudflareinsights' in page:
        sys.exit(f'nd_render: REFUSING to write {where} — analytics beacon found in the email')
    return page

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
    out = []; in_signoff = False; signed = False
    def close():
        nonlocal in_signoff
        if in_signoff: out.append('</div>'); in_signoff = False
    for b in d['blocks']:
        t = b['t']
        if t not in ('note','ask','next','follow'): close()
        if t == 'dek':
            out.append(f'<div class="dek"><p>{b["html"]}</p></div>')
            out.append(form_block(kick='Tomorrow\u2019s edition, 6 AM Eastern.', sub='Confirmed news kept apart from rumor. One email. Free.', extra_class='inline'))
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
            elif t == 'ask': out.append(f'<p class="ask">{b["html"]}</p><p class="byline">{esc(BYLINE)}</p>' + share_block(d['n'], d['title'])); signed = True
            elif t == 'next': out.append(f'<div class="next"><b>Next edition</b><span>{esc(b["text"])}</span></div>')
            elif t == 'follow':
                links = ' · '.join(f'<a href="{esc(l["url"])}" rel="noopener">{esc(l["label"])}</a>' for l in b['links'])
                out.append(f'<p class="follow">FOLLOW {links}</p>')
        elif t == 'sources':
            if not signed:   # editions without an 'ask' block (10-12) still get the byline + share line
                out.append(f'<div class="signoff"><p class="byline">{esc(BYLINE)}</p>' + share_block(d['n'], d['title']) + '</div>'); signed = True
            out.append(prev_next(d['n']))
            out.append(cta_band())
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
            f'<title>{esc(title)} — Nerazzurri Daily No. {n}</title>'
            + meta(title, desc, f'{SITE}/p/edition-{n}/', f'{SITE}/assets/mast/edition-{n:02d}.png', 'article', d['date'])
            + jsonld_article(n, title, desc, d['date'], f'{SITE}/assets/mast/edition-{n:02d}.png')
            + f'{FONTS}\n{SIB_CSS}\n<style>{CSS}{FORM_CSS}</style></head>')
    body = (f'<body><div class="sheet">\n<div class="top"><a class="wm" href="/">NERAZZURRI <b>DAILY</b></a><span class="util">Edition No. {n} · {shortdate(d["date"])} · <a href="#subscribe">Subscribe</a></span></div>'
            f'<h1 class="sr">{esc(title)}</h1><img class="mast" src="/assets/mast/edition-{n:02d}.png" alt="{esc(alt)}">'
            + page_blocks(d) +
            '<div class="foot">Fan-made. Not affiliated with FC Internazionale Milano.<br>\n<a href="#subscribe">Subscribe</a> &middot; <a href="/">All editions</a> &middot; <a href="/fixtures/">Fixtures</a> &middot; <a href="https://www.youtube.com/@nerazzurridaily" rel="noopener">YouTube</a> &middot; <a href="https://www.tiktok.com/@nerazzurridaily" rel="noopener">TikTok</a></div>\n</div>\n'
            + STICK + HOME_FORM_JS + PN_JS + SHARE_JS + '\n</body></html>\n')
    return require_signup_form(head + body, f'p/edition-{n}/index.html')

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
            elif t == 'ask':
                rows.append(P(b['html'], 17, '#3D465C', 18, 0)); rows.append(P(esc(BYLINE), 13, '#5A647E', 14, 0, MONO))
                rows.append(P(f'Know an Interista? Forward this email \u2014 they can subscribe at <a href="{door_url("forward", n)}" style="color:#0A2A66;">nerazzurridaily.com/subscribe</a>.', 13, '#5A647E', 10, 0, MONO))
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
    R(f'<div style="font-family:{MONO};font-size:13px;color:#5A647E;line-height:1.9;">Fan-made. Not affiliated with FC Internazionale Milano.<br><a href="{SITE}/subscribe/" style="color:#0A2A66;">Subscribe</a> &middot; <a href="{SITE}/" style="color:#0A2A66;">All editions</a> &middot; <a href="https://www.youtube.com/@nerazzurridaily" style="color:#0A2A66;">YouTube</a> &middot; <a href="https://www.tiktok.com/@nerazzurridaily" style="color:#0A2A66;">TikTok</a></div>', '#DCE3EF', '18px 28px')
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

# ------------------------------------------------------------------ /subscribe/ (the short landing page for bios and social links)
SUB_CSS = """
.sub-hero{padding:26px 28px 6px}
.sub-hero h1{font-family:Oswald,sans-serif;font-size:32px;line-height:1.1;color:#0B1020;margin:0 0 10px;text-wrap:balance}
.sub-hero p{font-size:17px;line-height:1.6;margin:0 0 12px}
.promise{margin:18px 28px 0;padding:0;list-style:none;display:grid;gap:10px}
.promise li{border-left:5px solid #2B5BB8;background:#EEF1F6;padding:10px 14px;font-size:16px;line-height:1.5}
.promise li.r{border-left-color:#E7B4AE;background:#FBEAE7}
.promise b{font-family:Oswald,sans-serif;font-size:15px;letter-spacing:.06em;text-transform:uppercase;color:#0B1020;display:block;margin-bottom:2px}
@media(max-width:520px){.sub-hero{padding-left:16px;padding-right:16px}.promise{margin-left:16px;margin-right:16px}}
"""
def render_subscribe(count, first_iso):
    desc = 'Inter Milan in English, every morning, in 90 seconds \u2014 what the club has confirmed, kept apart from what the papers are only reporting. Free.'
    page = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<title>Subscribe \u2014 Nerazzurri Daily</title>'
            + meta('Subscribe to Nerazzurri Daily', desc, f'{SITE}/subscribe/', OG_BRAND)
            + f'{FONTS}\n{SIB_CSS}\n<style>{CSS}{FORM_CSS}{SUB_CSS}</style></head><body><div class="sheet">\n'
            f'<div class="top"><a class="wm" href="/">NERAZZURRI <b>DAILY</b></a><span class="util">{count} editions · <a href="/">All editions</a></span></div>\n'
            f'<div class="sub-hero"><h1>{esc(HEADLINE)}</h1><p>{esc(SUBLINE)}</p></div>\n'
            '<ul class="promise">\n'
            '<li><b>Confirmed</b>What the club, the league or UEFA has actually said \u2014 with the source and the date on every item.</li>\n'
            '<li class="r"><b>Reported</b>What the Italian papers are saying, kept apart from the facts and attributed to the outlet that broke it.</li>\n'
            '<li><b>Next up</b>Every fixture with the Eastern kickoff, the Milan time and the US broadcaster once it is published.</li>\n'
            '</ul>\n'
            + form_block(head='Subscribe', sub='The Kickoff Card \u2014 all 38 Serie A dates as a phone wallpaper \u2014 comes with your welcome email.') + proof_line(count, first_iso) +
            '<div class="sub-hero"><p class="fine">Not sure yet? <a href="/">Read any past edition</a> first.</p></div>\n'
            '<div class="foot">Fan-made. Not affiliated with FC Internazionale Milano.<br>\n<a href="/">All editions</a> &middot; <a href="https://www.youtube.com/@nerazzurridaily" rel="noopener">YouTube</a> &middot; <a href="https://www.tiktok.com/@nerazzurridaily" rel="noopener">TikTok</a></div>\n'
            '</div>\n' + HOME_FORM_JS + '\n</body></html>\n')
    return require_signup_form(require_beacon(page, 'subscribe/index.html'), 'subscribe/index.html')

# ------------------------------------------------------------------ today's edition card (home hero)
def strip_tags(h):
    from bs4 import BeautifulSoup
    return BeautifulSoup(h, 'html.parser').get_text()

def today_card():
    """The newest JSON edition as an overlapping card: masthead, dek, first CONFIRMED and first REPORTED item."""
    paths = sorted(glob.glob('data/edition-*.json'), key=lambda p: int(re.search(r'edition-(\d+)', p).group(1)))
    if not paths: return ''
    d = json.load(open(paths[-1], encoding='utf-8')); n = d['n']
    dek = next((strip_tags(b['html']) for b in d['blocks'] if b['t'] == 'dek'), '')
    if len(dek) > 210: dek = dek[:207].rsplit(' ', 1)[0] + '\u2026'
    conf = next((strip_tags(b['h3']) for b in d['blocks'] if b['t'] == 'item' and not b.get('rep')), None)
    repd = next((strip_tags(b['h3']) for b in d['blocks'] if b['t'] == 'item' and b.get('rep')), None)
    items = (f'<div class="ci"><small>CONFIRMED</small>{esc(conf)}</div>' if conf else '') + (f'<div class="ci rep"><small>REPORTED</small>{esc(repd)}</div>' if repd else '')
    return (f'<a class="card" href="/p/edition-{n}/" aria-label="Read edition No. {n}"><img src="/assets/mast/edition-{n:02d}.png" alt="{esc(d.get("mast_alt") or d["title"])}">'
            f'<div class="cb"><p class="eyebrow">Today \u00b7 No. {n} \u00b7 {shortdate(d["date"])}</p><p class="cdek">{esc(dek)}</p>{items}'
            f'<span class="go">Read today\u2019s edition \u2192</span></div></a>')

# ------------------------------------------------------------------ /fixtures/ (evergreen: next up from the latest edition + the season calendar)
FIX_CSS = """
.fx-note{font-family:'Fragment Mono',monospace;font-size:.82rem;color:#5A647E;line-height:1.6;margin:6px 28px 0}
.season{width:100%;border-collapse:collapse;margin:6px 28px 0;width:calc(100% - 56px)}
.season td{padding:8px 0;border-bottom:1px solid #D8DFEC;vertical-align:baseline}
.season .md{font-family:'Fragment Mono',monospace;font-size:.82rem;color:#5A647E;width:36px}
.season .dt{font-family:'Fragment Mono',monospace;font-size:.82rem;color:#3D465C;width:120px;white-space:nowrap}
.season .op{font-family:Oswald,sans-serif;font-weight:700;font-size:17px;color:#0B1020}
.season .op i{display:inline-block;width:8px;height:8px;border-radius:50%;background:#E7B4AE;margin-left:8px;vertical-align:1px}
.season .ha{text-align:right}
@media(max-width:520px){.fx-note{margin-left:16px;margin-right:16px}.season{margin-left:16px;width:calc(100% - 32px)}.season .dt{width:96px;white-space:normal}}
"""
def render_fixtures(count, first_iso):
    paths = sorted(glob.glob('data/edition-*.json'), key=lambda p: int(re.search(r'edition-(\d+)', p).group(1)))
    latest = json.load(open(paths[-1], encoding='utf-8')) if paths else {'blocks': [], 'n': 0}
    fx = next((b for b in latest['blocks'] if b['t'] == 'fixtures'), None)
    note = next((b['html'] for b in latest['blocks'] if b['t'] == 'note'), '')
    season = json.load(open('data/season-2026-27.json', encoding='utf-8'))
    title = 'Inter fixtures in Eastern time, with US TV'
    desc = ('Every upcoming Inter Milan match with the Eastern kickoff, the Milan time and the US broadcaster, plus all 38 Serie A dates of 2026-27. '
            'Updated every morning by Nerazzurri Daily.')
    rows = ''.join(f'<tr><td><div class="nm">{chip(r["name"], r.get("venue"))}</div><div class="meta">{nbsp(r["line2"])}</div>'
                   f'<div class="tm">{et_bold(nbsp(r["line3"]))}</div></td></tr>' for r in (fx['rows'] if fx else []))
    big = {'Milan', 'Juventus', 'Napoli'}
    srows = ''.join(f'<tr><td class="md">{r["md"]:02d}</td><td class="dt">{esc(r["dates"])}</td><td class="op">{esc(r["opponent"])}{"<i></i>" if r["opponent"] in big else ""}</td>'
                    f'<td class="ha"><span class="chip">{r["venue"]}</span></td></tr>' for r in season['rows'])
    page = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<title>{title} \u2014 Nerazzurri Daily</title>'
            + meta(title, desc, f'{SITE}/fixtures/', OG_BRAND)
            + f'{FONTS}\n{SIB_CSS}\n<style>{CSS}{FORM_CSS}{FIX_CSS}</style></head><body><div class="sheet">\n'
            f'<div class="top"><a class="wm" href="/">NERAZZURRI <b>DAILY</b></a><span class="util">{count} editions · <a href="#subscribe">Subscribe</a></span></div>\n'
            f'<div class="hero"><h1>Inter fixtures in Eastern time.</h1><p>Every kickoff in ET first, Milan time second, and the US broadcaster once it is published. '
            f'Kept current every morning from <a href="/p/edition-{latest.get("n", "")}/">the latest edition</a>.</p></div>\n'
            + form_block(head='Every kickoff in your inbox', fine='Free \u00b7 one email a morning with the next match at the top \u00b7 unsubscribe any time')
            + f'<div class="sec"><b>Next up</b><em>EASTERN TIME FIRST, MILAN SECOND</em></div><div class="in"><table class="sb"><tbody>{rows}</tbody></table></div>'
            + (f'<p class="fx-note">{note}</p>' if note else '')
            + f'<div class="sec"><b>Serie A 2026-27 \u00b7 all 38</b><em>WEEKEND WINDOWS FROM INTER.IT</em></div>'
            f'<table class="season"><tbody>{srows}</tbody></table>'
            f'<p class="fx-note">Dates are the league\u2019s weekend windows ({esc(season["source"])}); the exact day and the Eastern kickoff appear above once Serie A sets them. '
            f'The pink dot marks the derby, Juventus and Napoli. HOME is San Siro.</p>'
            + cta_band().replace('class="ctaband"', 'class="ctaband end"') +
            '<div class="foot">Fan-made. Not affiliated with FC Internazionale Milano.<br>\n<a href="#subscribe">Subscribe</a> &middot; <a href="/">All editions</a> &middot; <a href="/fixtures/">Fixtures</a> &middot; <a href="https://www.youtube.com/@nerazzurridaily" rel="noopener">YouTube</a> &middot; <a href="https://www.tiktok.com/@nerazzurridaily" rel="noopener">TikTok</a></div>\n'
            '</div>\n' + STICK + HOME_FORM_JS + '\n</body></html>\n')
    return require_signup_form(require_beacon(page, 'fixtures/index.html'), 'fixtures/index.html')

# ------------------------------------------------------------------ /feed.xml (RSS 2.0, every edition)
def render_feed(eds):
    import email.utils
    descs = {}
    for p in glob.glob('data/edition-*.json'):
        d = json.load(open(p, encoding='utf-8')); descs[d['n']] = d.get('description', '')
    items = ''
    for n, dt, t in eds:
        pub = email.utils.format_datetime(datetime.datetime.fromisoformat(dt + 'T05:30:00').replace(tzinfo=datetime.timezone(datetime.timedelta(hours=int(et_offset(dt)[:3])))))
        items += (f'  <item><title>{esc(t)}</title><link>{SITE}/p/edition-{n}/</link><guid isPermaLink="true">{SITE}/p/edition-{n}/</guid>'
                  f'<pubDate>{pub}</pubDate><description>{esc(descs.get(n) or t)}</description></item>\n')
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>\n'
            f'  <title>Nerazzurri Daily</title><link>{SITE}/</link><atom:link href="{SITE}/feed.xml" rel="self" type="application/rss+xml"/>\n'
            '  <description>Inter Milan in English, every morning, in 90 seconds \u2014 what the club has confirmed, kept apart from what the papers are only reporting.</description>'
            '<language>en-us</language>\n' + items + '</channel></rss>\n')

# ------------------------------------------------------------------ index + sitemap
def build_index():
    eds = []
    for p in glob.glob('data/edition-*.json'):
        d = json.load(open(p, encoding='utf-8')); eds.append((d['n'], d['date'], d['title']))
    if os.path.exists('data/legacy.json'):
        for e in json.load(open('data/legacy.json', encoding='utf-8')): eds.append((e['n'], e['date'], e['title']))
    eds = sorted({e[0]: e for e in eds}.values(), key=lambda e: -e[0])
    lis = ''.join(f'<li><span class="d">No. {n} &middot; {longdate(dt)}</span><a class="t" href="p/edition-{n}/">{esc(t)}</a></li>' for n, dt, t in eds)
    first = min(e[1] for e in eds)
    home_desc = 'Inter Milan in English, every morning, in 90 seconds \u2014 what the club has confirmed, kept apart from what the papers are only reporting, with the source and date on every item. Free.'
    page = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<title>Nerazzurri Daily \u2014 Inter Milan in English, every morning</title>'
            + meta('Nerazzurri Daily \u2014 Inter Milan in English, every morning', home_desc, f'{SITE}/', OG_BRAND)
            + f'{FONTS}\n{SIB_CSS}\n<style>{CSS}{FORM_CSS}{HOME_CSS}</style></head>'
            f'<body><div class="sheet">\n<div class="top"><a class="wm" href="./">NERAZZURRI <b>DAILY</b></a><span class="util">{len(eds)} editions · <a href="/fixtures/">Fixtures (ET)</a> · <a href="#subscribe">Subscribe</a></span></div>\n'
            f'<div class="hero2"><div><h1 class="hero-h">{esc(HEADLINE)}</h1><p class="hero-p">{esc(SUBLINE)}</p>'
            + form_block(head='Get it every morning', sub='Subscribe and the Kickoff Card \u2014 all 38 Serie A dates as a phone wallpaper \u2014 comes with your welcome email.') + proof_line(len(eds), first) + '</div>'
            + today_card() + '</div>\n'
            '<div class="three">'
            '<div><b>Confirmed</b>What the club, the league or UEFA has actually said \u2014 with the source and the date on every item.</div>'
            '<div class="r"><b>Reported</b>What the Italian papers are saying, kept apart from the facts and attributed to the outlet that broke it.</div>'
            '<div><b>Next up</b>Every fixture with the Eastern kickoff, the Milan time and the US broadcaster once it is published.</div></div>\n'
            f'<div class="who"><div class="mk">ND</div><div><b>{esc(WHO_HEAD)}</b><p>{esc(WHO)}</p></div></div>\n'
            f'<div class="idx compact"><h2>Every edition</h2><p class="sub">Every morning since No. 1 \u2014 sorted into what is confirmed and what is only reported.</p><ul>{lis}</ul></div>'
            + cta_band().replace('class="ctaband"', 'class="ctaband end"') +
            '<div class="foot">Fan-made. Not affiliated with FC Internazionale Milano.<br>\n<a href="#subscribe">Subscribe</a> &middot; <a href="./">All editions</a> &middot; <a href="/fixtures/">Fixtures</a> &middot; <a href="https://www.youtube.com/@nerazzurridaily" rel="noopener">YouTube</a> &middot; <a href="https://www.tiktok.com/@nerazzurridaily" rel="noopener">TikTok</a></div>\n</div>\n' + HOME_FORM_JS + '\n</body></html>\n')
    require_beacon(page, 'index.html')  # checked BEFORE open(): open('w') truncates the live file
    require_signup_form(page, 'index.html')
    open('index.html', 'w', encoding='utf-8').write(page)
    sub = render_subscribe(len(eds), first)
    os.makedirs('subscribe', exist_ok=True); open('subscribe/index.html', 'w', encoding='utf-8').write(sub)
    fx = render_fixtures(len(eds), first)
    os.makedirs('fixtures', exist_ok=True); open('fixtures/index.html', 'w', encoding='utf-8').write(fx)
    open('feed.xml', 'w', encoding='utf-8').write(render_feed(eds))
    for ch in DOORS:
        os.makedirs(f'go/{ch}', exist_ok=True); open(f'go/{ch}/index.html', 'w', encoding='utf-8').write(render_door(ch))
    urls = [(f'{SITE}/', eds[0][1]), (f'{SITE}/subscribe/', eds[0][1]), (f'{SITE}/fixtures/', eds[0][1])] + [(f'{SITE}/p/edition-{n}/', dt) for n, dt, _ in eds]
    open('sitemap.xml', 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'  <url><loc>{u}</loc><lastmod>{dt}</lastmod></url>\n' for u, dt in urls) + '</urlset>\n')
    return len(eds)

if __name__ == '__main__':
    if '--index' in sys.argv: print('index + subscribe + fixtures + feed + sitemap:', build_index(), 'editions'); sys.exit()
    for p in [a for a in sys.argv[1:] if a.endswith('.json')]:
        d = json.load(open(p, encoding='utf-8')); n = d['n']
        # a plain paragraph right after the fixtures table is the kickoff note
        for i, b in enumerate(d['blocks']):
            if b['t'] == 'p' and i and d['blocks'][i-1]['t'] == 'fixtures': b['t'] = 'note'
        os.makedirs(f'p/edition-{n}', exist_ok=True); os.makedirs('build', exist_ok=True)
        page = require_beacon(render_page(d), f'p/edition-{n}/index.html'); email = forbid_beacon(render_email(d), f'build/email-{n}.html')  # both checked before any file is opened
        open(f'p/edition-{n}/index.html', 'w', encoding='utf-8').write(page)
        open(f'build/email-{n}.html', 'w', encoding='utf-8').write(email)
        open(f'build/edition-{n}.txt', 'w', encoding='utf-8').write(render_text(d))
        assert os.path.exists(f'assets/mast/edition-{n:02d}.png'), f'missing masthead assets/mast/edition-{n:02d}.png'
        print(f'edition {n}: page, build/email-{n}.html, build/edition-{n}.txt')
