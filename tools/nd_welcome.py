#!/usr/bin/env python3
"""Welcome email for new Nerazzurri Daily subscribers (Brevo transactional).
Runs in the Composio workbench after exec(open('tools/nd_publish.py').read()) — it needs proxy_execute.

  template_sync()   -> creates or updates the transactional template "Nerazzurri Daily — Welcome" from templates/welcome-email.html; returns its id
  sweep(hours=2)    -> every contact confirmed into the "Nerazzurri Daily" list in the last `hours` that has no WELCOME_SENT
                       attribute gets the welcome email once, then WELCOME_SENT is stamped. Idempotent; safe to run often.
The attribute WELCOME_SENT (text) is created on first use. Nothing here ever sends a campaign.
"""
import datetime, json, os

TEMPLATE_NAME = 'Nerazzurri Daily — Welcome'
SUBJECT = "You’re in — and here’s your Kickoff Card"
SENDER = {'name': 'Nerazzurri Daily', 'email': 'mail@nerazzurridaily.com'}
LIST_NAME = 'Nerazzurri Daily'
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _bx(method, endpoint, **kw):
    r, e = proxy_execute(method=method, endpoint=endpoint, toolkit='brevo', **kw)
    if e: raise RuntimeError(f'brevo {method} {endpoint}: {e}')
    return _unwrap(r) if r is not None else {}

def list_id():
    for l in _bx('GET', '/contacts/lists', query_params={'limit': '50'}).get('lists', []):
        if l['name'] == LIST_NAME: return l['id']
    raise RuntimeError('list not found')

def ensure_attribute():
    names = {a['name'] for a in _bx('GET', '/contacts/attributes').get('attributes', [])}
    if 'WELCOME_SENT' not in names:
        _bx('POST', '/contacts/attributes/normal/WELCOME_SENT', body={'type': 'text'})

def template_sync():
    html = open(os.path.join(ROOT, 'templates', 'welcome-email.html'), encoding='utf-8').read()
    for t in _bx('GET', '/smtp/templates', query_params={'limit': '50'}).get('templates', []):
        if t['name'] == TEMPLATE_NAME:
            _bx('PUT', f"/smtp/templates/{t['id']}", body={'htmlContent': html, 'subject': SUBJECT, 'sender': SENDER, 'replyTo': SENDER['email'], 'isActive': True})
            return t['id']
    r = _bx('POST', '/smtp/templates', body={'templateName': TEMPLATE_NAME, 'htmlContent': html, 'subject': SUBJECT, 'sender': SENDER, 'replyTo': SENDER['email'], 'isActive': True})
    return r['id']

def sweep(hours=2, dry=False):
    ensure_attribute(); lid = list_id(); tid = template_sync()
    since = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    sent, skipped = [], []
    cs = _bx('GET', '/contacts', query_params={'listIds': str(lid), 'modifiedSince': since, 'limit': '500'}).get('contacts', [])
    for c in cs:
        if lid not in (c.get('listIds') or []) or c.get('emailBlacklisted'): continue
        if (c.get('attributes') or {}).get('WELCOME_SENT'): skipped.append(c['email']); continue
        if not dry:
            _bx('POST', '/smtp/email', body={'to': [{'email': c['email']}], 'templateId': tid, 'tags': ['welcome']})
            _bx('PUT', f"/contacts/{c['id']}", body={'attributes': {'WELCOME_SENT': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%MZ')}})
        sent.append(c['email'])
    return {'template_id': tid, 'window_hours': hours, 'candidates': len(cs), 'sent': sent, 'already': skipped, 'dry': dry}
