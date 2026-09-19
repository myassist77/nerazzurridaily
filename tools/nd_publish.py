"""Publish helpers for the Composio REMOTE WORKBENCH (they need its proxy_execute). Load with:
    exec(open('/home/user/nd/site/tools/nd_publish.py').read())
then:
    sha = gh_commit(['p/edition-19/index.html','assets/mast/edition-19.png','data/edition-19.json','index.html','sitemap.xml'], 'Edition No. 19 — <headline>')
    cid = brevo_draft(19, subject, preview_text, '/home/user/nd/site/build/email-19.html')
Never schedules or sends: brevo_draft creates a DRAFT (no scheduled_at). The owner presses send.
"""
import base64, json, os, time, requests

REPO = '/repos/myassist77/nerazzurridaily'
ROOT = '/home/user/nd/site'
SENDER = 'mail@nerazzurridaily.com'
LIST_NAME = 'Nerazzurri Daily'
TRAILER = "\n\nCo-Authored-By: Claude <noreply@anthropic.com>"

def _unwrap(x):
    while isinstance(x, dict) and 'data' in x and isinstance(x['data'], dict): x = x['data']
    return x or {}

def gh_commit(paths, message, root=ROOT):
    """One commit with every path in `paths` (repo-relative, read from root). Returns the commit sha."""
    ref = _unwrap(proxy_execute(method='GET', endpoint=f'{REPO}/git/ref/heads/main', toolkit='github')[0]); head = ref['object']['sha']
    base_tree = _unwrap(proxy_execute(method='GET', endpoint=f'{REPO}/git/commits/{head}', toolkit='github')[0])['tree']['sha']
    tree = []
    for p in paths:
        content = open(os.path.join(root, p), 'rb').read()
        b, e = proxy_execute(method='POST', endpoint=f'{REPO}/git/blobs', toolkit='github', body={"content": base64.b64encode(content).decode(), "encoding": "base64"})
        if e: raise RuntimeError(f'blob {p}: {e}')
        tree.append({"path": p, "mode": "100644", "type": "blob", "sha": _unwrap(b)['sha']})
    t, e = proxy_execute(method='POST', endpoint=f'{REPO}/git/trees', toolkit='github', body={"base_tree": base_tree, "tree": tree})
    if e: raise RuntimeError(f'tree: {e}')
    c, e = proxy_execute(method='POST', endpoint=f'{REPO}/git/commits', toolkit='github', body={"message": message + TRAILER, "tree": _unwrap(t)['sha'], "parents": [head]})
    if e: raise RuntimeError(f'commit: {e}')
    sha = _unwrap(c)['sha']
    u, e = proxy_execute(method='PATCH', endpoint=f'{REPO}/git/refs/heads/main', toolkit='github', body={"sha": sha, "force": False})
    if e: raise RuntimeError(f'ref update: {e}')
    return sha

def gh_file_exists(path):
    r, e = proxy_execute(method='GET', endpoint=f'{REPO}/contents/{path}', toolkit='github')
    return not e

def wait_live(url, needle, tries=10, sleep=15):
    """Poll the live site until `needle` appears in the body (GitHub Pages builds take ~15-60 s)."""
    for i in range(tries):
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200 and needle in r.text: return True
        except Exception: pass
        time.sleep(sleep)
    return False

def brevo_list_id(name=LIST_NAME):
    ls = _unwrap(proxy_execute(method='GET', endpoint='/contacts/lists', toolkit='brevo', query_params={'limit': '50'})[0])
    for l in ls.get('lists', []):
        if l['name'].strip().lower() == name.lower(): return l['id']
    raise RuntimeError(f'Brevo list "{name}" not found; lists: {[l["name"] for l in ls.get("lists", [])]}')

def brevo_sender_id(email=SENDER):
    s = _unwrap(proxy_execute(method='GET', endpoint='/senders', toolkit='brevo')[0])
    for x in s.get('senders', []):
        if x['email'].lower() == email.lower() and x.get('active'): return x['id']
    raise RuntimeError(f'Brevo sender {email} not found/active')

def brevo_draft(n, subject, preview, html_path, name=None):
    """Create a DRAFT campaign (never scheduled). Returns the campaign id."""
    html = open(html_path, encoding='utf-8').read()
    body = {"name": name or f"Nerazzurri Daily No. {n} — {subject}"[:200], "subject": subject, "previewText": preview,
            "sender": {"id": brevo_sender_id(), "name": "Nerazzurri Daily", "email": SENDER}, "replyTo": SENDER,
            "htmlContent": html, "recipients": {"listIds": [brevo_list_id()]}, "mirrorActive": True}
    r, e = proxy_execute(method='POST', endpoint='/emailCampaigns', toolkit='brevo', body=body)
    if e: raise RuntimeError(f'brevo create: {e}')
    return _unwrap(r)['id']

def brevo_campaign(cid):
    c = _unwrap(proxy_execute(method='GET', endpoint=f'/emailCampaigns/{cid}', toolkit='brevo')[0])
    return {k: c.get(k) for k in ('id', 'name', 'subject', 'status', 'scheduledAt', 'sender', 'replyTo', 'recipients', 'previewText')} | {'html_bytes': len(c.get('htmlContent') or '')}

def brevo_today_campaign(n):
    """Re-run safety: an existing campaign whose name starts with 'Nerazzurri Daily No. {n} '."""
    c = _unwrap(proxy_execute(method='GET', endpoint='/emailCampaigns', toolkit='brevo', query_params={'limit': '20'})[0])
    for x in c.get('campaigns', []):
        if x.get('name', '').startswith(f'Nerazzurri Daily No. {n} '): return {k: x.get(k) for k in ('id', 'name', 'status', 'sentDate')}
    return None
