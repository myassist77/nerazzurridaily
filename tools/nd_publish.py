"""Publish helpers for the Composio REMOTE WORKBENCH (they need its proxy_execute). Load with:
    exec(open('/home/user/nd/tools/nd_publish.py').read())
then:
    sha = gh_commit(['p/edition-19/index.html','assets/mast/edition-19.png','data/edition-19.json','index.html','sitemap.xml'], 'Edition No. 19 — <headline>')
    cid = brevo_draft(19, subject, preview_text, '/home/user/nd/build/email-19.html')
Never schedules or sends: brevo_draft creates a DRAFT (no scheduled_at). The owner presses send.
"""
import base64, json, os, time, requests

REPO = '/repos/myassist77/nerazzurridaily'
ROOT = os.environ.get('ND_ROOT', '/home/user/nd')   # the checkout the scheduled run makes (Step 0.25); was /home/user/nd/site before Sept 19
SENDER = 'mail@nerazzurridaily.com'
LIST_ID = 4   # the "Nerazzurri Daily" contact list. Looked up BY ID since Oct 20, 2026 (owner's decision): the list was renamed
              # "Nerazzurri Daily Mailing List" and the by-name lookup raised. Its name may change; this id is the one Brevo keeps.
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

def brevo_list_id(list_id=LIST_ID):
    """The contact list, by ID (never by name — the name changed on Oct 20, 2026). Confirms the list exists and returns its id."""
    r, e = proxy_execute(method='GET', endpoint=f'/contacts/lists/{list_id}', toolkit='brevo')
    l = _unwrap(r) if not e else {}
    if e or l.get('id') != list_id:
        ls = _unwrap(proxy_execute(method='GET', endpoint='/contacts/lists', toolkit='brevo', query_params={'limit': '50'})[0])
        raise RuntimeError(f'Brevo list id {list_id} not found; lists: {[(x["id"], x["name"]) for x in ls.get("lists", [])]}')
    return l['id']

def brevo_sender_id(email=SENDER):
    s = _unwrap(proxy_execute(method='GET', endpoint='/senders', toolkit='brevo')[0])
    for x in s.get('senders', []):
        if x['email'].lower() == email.lower() and x.get('active'): return x['id']
    raise RuntimeError(f'Brevo sender {email} not found/active')

def brevo_draft(n, subject, preview, html_path, name=None):
    """Create a DRAFT campaign (never scheduled). Returns the campaign id."""
    html = open(html_path, encoding='utf-8').read()
    body = {"name": name or f"Nerazzurri Daily No. {n} — {subject}"[:200], "subject": subject, "previewText": preview,
            "sender": {"name": "Nerazzurri Daily", "email": SENDER}, "replyTo": SENDER,
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

# ---- Since Oct 21, 2026: the edition is built and committed by .github/workflows/edition.yml, not here. --------------
# The Composio sandbox lost outbound network and github proxy execution on Oct 19-20, 2026, so gh_commit() and
# wait_live() above cannot run in it. The morning run commits data/edition-N.json with the GITHUB_COMMIT_MULTIPLE_FILES
# tool (a direct tool call), the workflow builds and commits the rest, and these helpers read what it left in the repo
# through the GITHUB_GET_REPOSITORY_CONTENT tool (run_composio_tool, which works where proxy_execute for github does not).
import hashlib

def repo_file(path, ref='main'):
    """Bytes of a file on the repo, read through the GitHub content tool (not the proxy)."""
    r, e = run_composio_tool('GITHUB_GET_REPOSITORY_CONTENT', {"owner": "myassist77", "repo": "nerazzurridaily", "path": path, "ref": ref})
    if e: raise RuntimeError(f'repo_file {path}: {e}')
    d = r
    for _ in range(4):
        if isinstance(d, dict) and 'data' in d: d = d['data']
    c = d.get('content') if isinstance(d, dict) else None
    if isinstance(c, dict): c = c.get('content')
    if not isinstance(c, str): raise RuntimeError(f'repo_file {path}: no content in response')
    return base64.b64decode(c)

def edition_status(n, ref='main'):
    """review/edition-N/status.json as the edition workflow committed it (None if it is not there yet)."""
    try: return json.loads(repo_file(f'review/edition-{n}/status.json', ref).decode('utf-8'))
    except Exception: return None

def brevo_draft_from_repo(n, subject, preview, name=None, dry_run=False):
    """Create the DRAFT campaign from review/edition-N/email-N.html, after checking its md5 against status.json.
    dry_run=True only fetches and verifies. Returns the campaign id (or the md5 on a dry run). Never sends."""
    st = edition_status(n)
    if not st or not st.get('passed'): raise RuntimeError(f'edition {n}: no passing status.json in the repo (got {st and st.get("steps")})')
    raw = repo_file(f'review/edition-{n}/email-{n}.html')
    md5 = hashlib.md5(raw).hexdigest()
    if md5 != (st.get('email') or {}).get('md5'): raise RuntimeError(f'edition {n}: email md5 {md5} != status.json {st.get("email")}')
    if dry_run: return md5
    html = raw.decode('utf-8')
    body = {"name": name or f"Nerazzurri Daily No. {n} — {subject}"[:200], "subject": subject, "previewText": preview,
            "sender": {"name": "Nerazzurri Daily", "email": SENDER}, "replyTo": SENDER,
            "htmlContent": html, "recipients": {"listIds": [brevo_list_id()]}, "mirrorActive": True}
    r, e = proxy_execute(method='POST', endpoint='/emailCampaigns', toolkit='brevo', body=body)
    if e: raise RuntimeError(f'brevo create: {e}')
    return _unwrap(r)['id']
