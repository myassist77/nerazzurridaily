#!/usr/bin/env python3
"""nd_bsky.py - answer the people who talk to us on Bluesky. Nobody else.

Runs only inside .github/workflows/bluesky.yml. The repo is public, so who wrote to us,
what they wrote and what we answer are kept ENCRYPTED (Fernet, secret OUTREACH_KEY):
  growth/community/bsky-state.enc  written here: the inbox (people waiting), what was sent
  growth/community/bsky-queue.enc  written by the Community agent: the answers to send
  growth/community/bsky-status.json written here, counts only, no handles, no text
Never print a handle, a post or a reply: the run log is public.

Modes: selftest | read | send | all (send what is queued, then read new notifications).

Rules enforced here, whatever the queue says (Bluesky asks automated accounts to interact
only with people who tagged them - docs.bsky.app/docs/starter-templates/bots):
  - we only ever REPLY, and only to a post that reached us as a notification of kind
    reply, mention or quote, written by someone else. No reply to a stranger, ever.
  - no like, no repost, no follow, no direct message, no new top-level post from here.
  - one answer per post; at most MAX_PER_THREAD answers of ours to one person in one thread;
    MAX_PER_RUN a run, MAX_PER_DAY a day.
  - 300 characters at most; a link only to nerazzurridaily.com and only one; no owner name.
  - never to an account that blocks or mutes us, or that we block or mute.
"""
import os, sys, json, re, time, datetime as dt, urllib.request, urllib.parse, urllib.error
from cryptography.fernet import Fernet

PDS = os.environ.get("BSKY_HOST", "https://bsky.social")
IDENT = os.environ.get("BSKY_IDENTIFIER", "did:plc:cqmhtmzyxdkm64ijvdddywbg")
PASSWORD = os.environ.get("BLUESKY_APP_PASSWORD", "")
KEY = os.environ.get("OUTREACH_KEY", "")
DIR = os.environ.get("COMMUNITY_DIR", "growth/community")
DRY = os.environ.get("DRY_RUN") == "1"
MAX_PER_RUN, MAX_PER_DAY, MAX_PER_THREAD, MAX_AGE_DAYS = 10, 30, 3, 14
KINDS = ("reply", "mention", "quote")
BANNED = ("macrina",)
OUR_SITE = "nerazzurridaily.com"
URL_RE = re.compile(r"https?://[^\s<>\"')\]]+")

def now(): return dt.datetime.now(dt.timezone.utc)
def iso(t=None): return (t or now()).strftime("%Y-%m-%dT%H:%M:%SZ")
def today(): return now().strftime("%Y-%m-%d")

def load(name, default):
    p = os.path.join(DIR, name)
    if not os.path.exists(p): return default
    raw = open(p, "rb").read().strip()
    if not raw: return default
    return json.loads(Fernet(KEY.encode()).decrypt(raw).decode())

def save(name, obj):
    os.makedirs(DIR, exist_ok=True)
    open(os.path.join(DIR, name), "wb").write(Fernet(KEY.encode()).encrypt(json.dumps(obj).encode()) + b"\n")

def write_status(**kw):
    """Public file: counts and generic words only. Rewritten only when something changed."""
    os.makedirs(DIR, exist_ok=True)
    p = os.path.join(DIR, "bsky-status.json")
    old = json.load(open(p)) if os.path.exists(p) else {}
    new = dict(old); new.update(kw)
    strip = lambda d: {k: v for k, v in d.items() if k != "last_change_utc"}
    if strip(new) == strip(old) and old: return
    new["last_change_utc"] = iso()
    json.dump(new, open(p, "w"), indent=1); open(p, "a").write("\n")

class Api:
    def __init__(self): self.jwt = None; self.did = None
    def call(self, method, nsid, params=None, body=None):
        url = f"{PDS}/xrpc/{nsid}"
        if params: url += "?" + urllib.parse.urlencode(params, doseq=True)
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        if data is not None: req.add_header("Content-Type", "application/json")
        if self.jwt: req.add_header("Authorization", "Bearer " + self.jwt)
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
        return json.loads(raw) if raw else {}
    def login(self):
        s = self.call("POST", "com.atproto.server.createSession", body={"identifier": IDENT, "password": PASSWORD})
        self.jwt, self.did = s["accessJwt"], s["did"]
        return s

def parse_time(s):
    try: return dt.datetime.fromisoformat((s or "").replace("Z", "+00:00"))
    except Exception: return None

def facets(text):
    """Make each URL in the text a tappable link (byte offsets, as the protocol wants)."""
    out = []
    for m in URL_RE.finditer(text):
        url = m.group(0).rstrip(".,;:!?")
        start = len(text[:m.start()].encode("utf-8"))
        out.append({"index": {"byteStart": start, "byteEnd": start + len(url.encode("utf-8"))},
                    "features": [{"$type": "app.bsky.richtext.facet#link", "uri": url}]})
    return out

def empty_state(): return {"inbox": {}, "sent": {}, "seen_until": None}

def allowed(item, state, our_did):
    """Return (ok, reason). Reasons are generic words, safe for the public log."""
    to = item.get("to"); text = (item.get("text") or "").strip()
    if not to or not text: return False, "incomplete"
    n = state["inbox"].get(to)
    if not n: return False, "not-addressed-to-us"            # the opt-in rule
    if n.get("reason") not in KINDS: return False, "not-addressed-to-us"
    if n.get("did") == our_did: return False, "self"
    if n.get("status") == "answered" or to in state["sent"]: return False, "already-answered"
    if n.get("blocked"): return False, "blocked-or-muted"
    if len(text) > 300: return False, "too-long"
    if any(b in text.lower() for b in BANNED): return False, "names-owner"
    urls = URL_RE.findall(text)
    if len(urls) > 1: return False, "two-links"
    if urls and OUR_SITE not in urllib.parse.urlparse(urls[0]).netloc: return False, "foreign-link"
    root = (n.get("root") or {}).get("uri") or to
    same = [s for s in state["sent"].values() if s.get("root") == root and s.get("did") == n.get("did")]
    if len(same) >= MAX_PER_THREAD: return False, "thread-limit"
    if sum(1 for s in state["sent"].values() if s.get("date", "")[:10] == today()) >= MAX_PER_DAY: return False, "day-limit"
    return True, "ok"

def do_send(api, state):
    queue = load("bsky-queue.enc", [])
    if not queue: return 0, [], False
    sent, refused = 0, []
    for item in queue:
        to = item.get("to")
        if item.get("skip"):                                   # the agent decided not to answer
            if to in state["inbox"] and state["inbox"][to].get("status") == "waiting":
                state["inbox"][to]["status"] = "flagged" if item.get("why") == "flag" else "skipped"
            continue
        if sent >= MAX_PER_RUN: refused.append("run-limit"); continue
        ok, why = allowed(item, state, api.did)
        if not ok: refused.append(why); continue
        n = state["inbox"][to]; text = item["text"].strip()
        rec = {"$type": "app.bsky.feed.post", "text": text, "createdAt": now().isoformat().replace("+00:00", "Z"),
               "langs": ["en"], "reply": {"root": n.get("root") or {"uri": n["uri"], "cid": n["cid"]},
                                          "parent": {"uri": n["uri"], "cid": n["cid"]}}}
        f = facets(text)
        if f: rec["facets"] = f
        try:
            if DRY: res = {"uri": "dry-run"}
            else: res = api.call("POST", "com.atproto.repo.createRecord",
                                 body={"repo": api.did, "collection": "app.bsky.feed.post", "record": rec})
        except urllib.error.HTTPError as e:
            refused.append("post-error-%s" % e.code); continue
        state["sent"][to] = {"date": iso(), "did": n.get("did"), "root": rec["reply"]["root"]["uri"], "uri": res.get("uri")}
        n["status"] = "answered"; sent += 1
        time.sleep(2)
    save("bsky-queue.enc", [])
    return sent, refused, True

def do_read(api, state):
    """Put new notifications addressed to us into the inbox. Returns (added, expired)."""
    cutoff = now() - dt.timedelta(days=MAX_AGE_DAYS)
    seen_until = parse_time(state.get("seen_until")) or (now() - dt.timedelta(days=7))
    added, newest, cursor = 0, seen_until, None
    for _ in range(5):
        p = {"limit": 100}
        if cursor: p["cursor"] = cursor
        page = api.call("GET", "app.bsky.notification.listNotifications", params=p)
        stop = False
        for n in page.get("notifications", []):
            at = parse_time(n.get("indexedAt"))
            if not at or at <= seen_until: stop = True; continue
            if at > newest: newest = at
            if n.get("reason") not in KINDS or at < cutoff: continue
            a = n.get("author") or {}
            if a.get("did") == api.did or n["uri"] in state["inbox"]: continue
            v = a.get("viewer") or {}
            rec = n.get("record") or {}
            rep = rec.get("reply") or {}
            state["inbox"][n["uri"]] = {
                "uri": n["uri"], "cid": n["cid"], "did": a.get("did"), "handle": a.get("handle"),
                "name": a.get("displayName"), "text": rec.get("text", ""), "reason": n["reason"], "at": n.get("indexedAt"),
                "root": rep.get("root"), "parent_uri": (rep.get("parent") or {}).get("uri"),
                "blocked": bool(v.get("blockedBy") or v.get("blocking") or v.get("muted")), "status": "waiting"}
            if state["inbox"][n["uri"]]["blocked"]: state["inbox"][n["uri"]]["status"] = "skipped"
            added += 1
        cursor = page.get("cursor")
        if stop or not cursor: break
    # what they were answering: the text of the post above theirs, so the agent has the context
    need = [n for n in state["inbox"].values() if n["status"] == "waiting" and n.get("parent_uri") and "parent_text" not in n]
    for i in range(0, len(need), 25):
        chunk = need[i:i + 25]
        try: posts = api.call("GET", "app.bsky.feed.getPosts", params={"uris": [n["parent_uri"] for n in chunk]}).get("posts", [])
        except urllib.error.HTTPError: posts = []
        by = {p["uri"]: p for p in posts}
        for n in chunk:
            p = by.get(n["parent_uri"]) or {}
            n["parent_text"] = (p.get("record") or {}).get("text", "")
            n["parent_is_ours"] = ((p.get("author") or {}).get("did") == api.did)
    # forget what is old: nothing waits for ever
    expired = 0
    for n in state["inbox"].values():
        at = parse_time(n.get("at"))
        if n["status"] == "waiting" and at and at < cutoff: n["status"] = "expired"; expired += 1
    state["seen_until"] = iso(newest)
    return added, expired

def main():
    mode = (sys.argv[1] if len(sys.argv) > 1 else "all").strip() or "all"
    if not KEY: print("no key"); write_status(error="no-key"); return 1
    if not PASSWORD:
        print("waiting for the app password"); write_status(waiting_for_password=True, error=None); return 0
    api = Api()
    try: s = api.login()
    except urllib.error.HTTPError as e:
        print("login failed", e.code); write_status(waiting_for_password=False, selftest_ok=False, error="login-%s" % e.code); return 1
    if mode == "selftest":
        ok = bool(s.get("did"))
        try: api.call("GET", "app.bsky.notification.listNotifications", params={"limit": 1}); can_read = True
        except urllib.error.HTTPError: can_read = False
        print("selftest", "ok" if ok and can_read else "failed")
        write_status(waiting_for_password=False, selftest_ok=ok and can_read, selftest_utc=iso(), error=None if ok and can_read else "cannot-read")
        return 0 if ok and can_read else 1
    state = load("bsky-state.enc", empty_state())
    sent, refused, had_queue = (0, [], False)
    if mode in ("send", "all"): sent, refused, had_queue = do_send(api, state)
    added, expired = do_read(api, state) if mode in ("read", "all") else (0, 0)
    waiting = sum(1 for n in state["inbox"].values() if n["status"] == "waiting")
    # seen_until moves on every read; the file is rewritten only when something real changed
    if added or sent or had_queue or expired:
        save("bsky-state.enc", state)
    print("sent", sent, "refused", len(refused), "new", added, "waiting", waiting)
    write_status(waiting_for_password=False, error=None, waiting=waiting, answered_total=len(state["sent"]),
                 last_refused=sorted(set(refused)), flagged=sum(1 for n in state["inbox"].values() if n["status"] == "flagged"))
    return 0

if __name__ == "__main__":
    sys.exit(main())
