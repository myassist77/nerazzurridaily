#!/usr/bin/env python3
"""nd_bsky_post.py - publish OUR OWN posts on Bluesky (the daily link post, the daily question).

Why this exists: until Nov 15, 2026 these posts went through Postiz. That morning Postiz lost
its Bluesky sign-in ("could not refresh your bluesky channel") and the edition was not posted,
while the task had already written "PUBLISHED". The owner chose to post from here instead:
this repo signs in with its own app password (secret BLUESKY_APP_PASSWORD, the one
tools/nd_bsky.py uses) and nothing has to be reconnected by hand.

Runs only inside .github/workflows/bluesky-post.yml. Nothing here is personal: the requests and
the results are plain files.
  data/links/bsky/ed<N>-<kind>.json  a REQUEST, committed by a task:
        {"n": 75, "kind": "link" | "question" | "video" | "ft" | "debate" | "pin", "text": "...",
         "image": "assets/mast/edition-75.png" (optional, a path in this repo), "alt": "...",
         "video": "assets/video/ed75.mp4" (optional, instead of an image; kinds "video", "ft" and "debate" need it)}
        Kind "ft" (since Nov 15, 2026) is the full-time card of a match played today: file
        ed<N>-ft.json, N = today's edition, "video": "assets/video/ft-<date>.mp4".
        Kind "debate" (since Nov 15, 2026) is THE DEBATE short posted today: file ed<N>-debate.json,
        N = today's edition, "video": "assets/video/debate-<date>-<slug>.mp4".
        A post carries a video OR an image, never both (Bluesky allows one kind of media a post).
        The video goes through Bluesky's video service (docs.bsky.app/docs/tutorials/video): a
        service token, upload to video.bsky.app, wait for the processing job, then the post. If
        that service fails, the file is uploaded as a plain blob instead and Bluesky processes it
        after the post exists. Hashtags in the text (#Inter) become tappable tags.
  data/links/bsky/sent.json          the RESULTS, written here, one entry per request file name:
        {"ed75-link": {"state": "PUBLISHED" | "ERROR", "uri", "url", "posted_at_utc",
                       "attempts", "error"}}
A task commits a request, waits, and reads sent.json: only "PUBLISHED" there means it is live
(this tool reads the post back from Bluesky before it writes that word).

Rules enforced here, whatever a request says:
  - one post per request file, ever: a request that already has a result is never sent again
    (PUBLISHED or ERROR). To send a failed one again, a person removes its entry from sent.json.
  - before sending, our own recent posts are read: if one has exactly this text, it is taken as
    already published and nothing is sent (no duplicate after a half-failed run).
  - only requests for an edition dated today or yesterday (New York) are sent; older ones are
    marked ERROR "stale". MAX_PER_DAY posts a day.
  - 300 characters at most; links only to nerazzurridaily.com, two at most; no owner name;
    never a reply, a like, a repost, a follow or a message (answers are nd_bsky.py's job).

Modes: selftest | post (default).
"""
import os, sys, json, re, glob, struct, time, datetime as dt, urllib.request, urllib.parse, urllib.error
from zoneinfo import ZoneInfo

PDS = os.environ.get("BSKY_HOST", "https://bsky.social")
IDENT = os.environ.get("BSKY_IDENTIFIER", "did:plc:cqmhtmzyxdkm64ijvdddywbg")
PASSWORD = os.environ.get("BLUESKY_APP_PASSWORD", "")
DIR = os.environ.get("BSKY_POST_DIR", "data/links/bsky")
DRY = os.environ.get("DRY_RUN") == "1"
HANDLE = "nerazzurridaily.com"
KINDS = ("link", "question", "video", "ft", "debate", "pin")
MAX_PER_DAY, MAX_ATTEMPTS, MAX_IMAGE, MAX_VIDEO = 5, 3, 950_000, 50_000_000
VIDEO_HOST = os.environ.get("BSKY_VIDEO_HOST", "https://video.bsky.app")
TAG_RE = re.compile(r"(?<![\w&/#])#([^\W\d_]\w{1,63})")
BANNED = ("macrina",)
OUR_SITE = "nerazzurridaily.com"
URL_RE = re.compile(r"https?://[^\s<>\"')\]]+")
NAME_RE = re.compile(r"^ed(\d+)-([a-z]+)$")

def now(): return dt.datetime.now(dt.timezone.utc)
def iso(t=None): return (t or now()).strftime("%Y-%m-%dT%H:%M:%SZ")
def ny_today(): return dt.datetime.now(ZoneInfo("America/New_York")).date()

class Api:
    def __init__(self): self.jwt = None; self.did = None; self.pds = None
    def call(self, method, nsid, params=None, body=None, raw=None, ctype=None, base=None, token=None, timeout=40):
        url = f"{base or PDS}/xrpc/{nsid}"
        if params: url += "?" + urllib.parse.urlencode(params, doseq=True)
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        req = urllib.request.Request(url, data=data, method=method)
        if data is not None: req.add_header("Content-Type", ctype or "application/json")
        if token or self.jwt: req.add_header("Authorization", "Bearer " + (token or self.jwt))
        with urllib.request.urlopen(req, timeout=timeout) as r:
            out = r.read()
        return json.loads(out) if out else {}
    def login(self):
        s = self.call("POST", "com.atproto.server.createSession", body={"identifier": IDENT, "password": PASSWORD})
        self.jwt, self.did = s["accessJwt"], s["did"]
        self.pds = None                                      # where the account's data lives
        for svc in (s.get("didDoc") or {}).get("service", []):
            if str(svc.get("id", "")).endswith("atproto_pds"): self.pds = (svc.get("serviceEndpoint") or "").rstrip("/") or None
        if not self.pds and self.did.startswith("did:plc:"):  # the session did not say: ask the directory
            try:
                with urllib.request.urlopen("https://plc.directory/" + self.did, timeout=20) as r: doc = json.loads(r.read())
                for svc in doc.get("service", []):
                    if str(svc.get("id", "")).endswith("atproto_pds"): self.pds = (svc.get("serviceEndpoint") or "").rstrip("/") or None
            except Exception: pass
        return s

def facets(text):
    """Make each URL in the text a tappable link (byte offsets, as the protocol wants)."""
    out = []
    for m in URL_RE.finditer(text):
        url = m.group(0).rstrip(".,;:!?")
        start = len(text[:m.start()].encode("utf-8"))
        out.append({"index": {"byteStart": start, "byteEnd": start + len(url.encode("utf-8"))},
                    "features": [{"$type": "app.bsky.richtext.facet#link", "uri": url}]})
    spans = [(m.start(), m.end()) for m in URL_RE.finditer(text)]
    for m in TAG_RE.finditer(text):                          # #Inter -> a tappable tag, never inside a link
        if any(a <= m.start() < b for a, b in spans): continue
        start = len(text[:m.start()].encode("utf-8"))
        out.append({"index": {"byteStart": start, "byteEnd": start + len(m.group(0).encode("utf-8"))},
                    "features": [{"$type": "app.bsky.richtext.facet#tag", "tag": m.group(1)}]})
    return sorted(out, key=lambda f: f["index"]["byteStart"])

def png_size(b):
    if b[:8] == b"\x89PNG\r\n\x1a\n": return struct.unpack(">II", b[16:24])
    return None

def check(name, req, results, edition_date):
    """Return (ok, reason). Reasons are short generic words."""
    m = NAME_RE.match(name)
    if not m: return False, "bad-file-name"
    if req.get("n") != int(m.group(1)) or req.get("kind") != m.group(2): return False, "name-does-not-match-request"
    if req["kind"] not in KINDS: return False, "unknown-kind"
    text = (req.get("text") or "").strip()
    if not text: return False, "no-text"
    if len(text) > 300: return False, "too-long"
    if any(b in text.lower() for b in BANNED): return False, "names-owner"
    urls = URL_RE.findall(text)
    if len(urls) > 2: return False, "too-many-links"
    for u in urls:
        host = urllib.parse.urlparse(u).netloc.lower()
        if host != OUR_SITE and not host.endswith("." + OUR_SITE): return False, "foreign-link"
    if req["kind"] != "pin":
        if edition_date is None: return False, "no-such-edition"
        if (ny_today() - edition_date).days not in (0, 1): return False, "stale"
    img = req.get("image")
    if img:
        if img.startswith("/") or ".." in img or not img.startswith("assets/") or not os.path.isfile(img): return False, "bad-image-path"
        if os.path.getsize(img) > MAX_IMAGE: return False, "image-too-large"
    vid = req.get("video")
    if req["kind"] in ("video", "ft", "debate") and not vid: return False, "no-video"
    if req["kind"] == "ft" and not re.match(r"^assets/video/ft-\d{4}-\d{2}-\d{2}\.mp4$", vid): return False, "not-a-full-time-video"
    if req["kind"] == "debate" and not re.match(r"^assets/video/debate-\d{4}-\d{2}-\d{2}-[a-z0-9-]+\.mp4$", vid): return False, "not-a-debate-video"
    if vid:
        if img: return False, "video-and-image"
        if vid.startswith("/") or ".." in vid or not vid.startswith("assets/video/") or not vid.endswith(".mp4") or not os.path.isfile(vid): return False, "bad-video-path"
        if os.path.getsize(vid) > MAX_VIDEO: return False, "video-too-large"
    day = iso()[:10]
    if sum(1 for r in results.values() if r.get("state") == "PUBLISHED" and (r.get("posted_at_utc") or "")[:10] == day) >= MAX_PER_DAY:
        return False, "day-limit"
    return True, "ok"

def edition_date(n):
    p = f"data/edition-{n}.json"
    try: return dt.date.fromisoformat(json.load(open(p))["date"])
    except Exception: return None

def find_existing(api, text):
    """Our own recent posts: one with exactly this text means it is already out."""
    got = api.call("GET", "com.atproto.repo.listRecords", params={"repo": api.did, "collection": "app.bsky.feed.post", "limit": 50})
    for r in got.get("records", []):
        if ((r.get("value") or {}).get("text") or "").strip() == text: return r.get("uri")
    return None

def video_size(req):
    """Width and height: from the request, else the social build record, else our 9:16 default."""
    if req.get("width") and req.get("height"): return int(req["width"]), int(req["height"])
    try:
        for st in json.load(open(f"review/social-ed{req['n']}/status.json")).get("streams", []):
            if st.get("codec_type") == "video": return int(st["width"]), int(st["height"])
    except Exception: pass
    return 1080, 1920

def upload_video(api, path):
    """Returns (blob, how). First the video service; if it fails, a plain blob on the account's server."""
    b = open(path, "rb").read()
    try:
        if not api.pds: raise RuntimeError("no-pds-in-session")
        aud = "did:web:" + urllib.parse.urlparse(api.pds).netloc
        tok = api.call("GET", "com.atproto.server.getServiceAuth", base=api.pds,
                       params={"aud": aud, "lxm": "com.atproto.repo.uploadBlob", "exp": int(time.time()) + 1800})["token"]
        try:
            job = api.call("POST", "app.bsky.video.uploadVideo", base=VIDEO_HOST, token=tok, raw=b, ctype="video/mp4",
                           params={"did": api.did, "name": os.path.basename(path)}, timeout=180)
        except urllib.error.HTTPError as e:                  # the same file again: the service answers 409 with the job
            if e.code != 409: raise
            job = json.loads(e.read().decode())
        job = job.get("jobStatus") or job
        if job.get("blob"): return job["blob"], "video-service"
        for _ in range(60):                                  # up to five minutes
            time.sleep(5)
            st = api.call("GET", "app.bsky.video.getJobStatus", base=VIDEO_HOST, token=tok, params={"jobId": job["jobId"]}).get("jobStatus", {})
            if st.get("blob"): return st["blob"], "video-service"
            if st.get("state") == "JOB_STATE_FAILED": raise RuntimeError("video-job-failed " + str(st.get("error") or st.get("message") or "")[:60])
        raise RuntimeError("video-job-timeout")
    except Exception as e:
        print("video service failed:", err_word(e), "- uploading as a plain blob")
        return api.call("POST", "com.atproto.repo.uploadBlob", base=api.pds, raw=b, ctype="video/mp4", timeout=180)["blob"], "plain-blob"

def post_url(uri): return f"https://bsky.app/profile/{HANDLE}/post/{uri.rsplit('/', 1)[-1]}"

def send(api, req):
    """Returns the uri of a post that was read back from Bluesky. Raises on failure."""
    text = req["text"].strip()
    uri = find_existing(api, text)
    if uri: return uri, True
    rec = {"$type": "app.bsky.feed.post", "text": text, "createdAt": now().isoformat().replace("+00:00", "Z"), "langs": ["en"]}
    f = facets(text)
    if f: rec["facets"] = f
    if req.get("image"):
        b = open(req["image"], "rb").read()
        mime = "image/png" if req["image"].lower().endswith(".png") else "image/jpeg"
        blob = api.call("POST", "com.atproto.repo.uploadBlob", raw=b, ctype=mime)["blob"]
        im = {"alt": (req.get("alt") or "")[:300], "image": blob}
        wh = png_size(b)
        if wh: im["aspectRatio"] = {"width": wh[0], "height": wh[1]}
        rec["embed"] = {"$type": "app.bsky.embed.images", "images": [im]}
    if req.get("video"):
        blob, how = upload_video(api, req["video"])
        w, h = video_size(req)
        rec["embed"] = {"$type": "app.bsky.embed.video", "video": blob, "aspectRatio": {"width": w, "height": h},
                        "alt": (req.get("alt") or "")[:900]}
        print("video uploaded through the", how)
    if DRY: return "at://dry/app.bsky.feed.post/dry", False
    res = api.call("POST", "com.atproto.repo.createRecord", body={"repo": api.did, "collection": "app.bsky.feed.post", "record": rec})
    uri = res["uri"]
    time.sleep(3)
    back = api.call("GET", "com.atproto.repo.getRecord", params={"repo": api.did, "collection": "app.bsky.feed.post", "rkey": uri.rsplit("/", 1)[-1]})
    if ((back.get("value") or {}).get("text") or "").strip() != text: raise RuntimeError("read-back-mismatch")
    return uri, False

def err_word(e):
    if isinstance(e, urllib.error.HTTPError):
        try: detail = json.loads(e.read().decode()).get("error", "")
        except Exception: detail = ""
        return ("http-%s %s" % (e.code, detail)).strip()
    if isinstance(e, urllib.error.URLError): return "network"
    return str(e)[:80] or e.__class__.__name__

def main():
    mode = (sys.argv[1] if len(sys.argv) > 1 else "post").strip() or "post"
    if not PASSWORD: print("no app password"); return 1
    api = Api()
    try: s = api.login()
    except Exception as e: print("login failed:", err_word(e)); api = None
    if mode == "selftest":
        ok = bool(api and s.get("did"))
        if ok:
            try: api.call("GET", "com.atproto.repo.listRecords", params={"repo": api.did, "collection": "app.bsky.feed.post", "limit": 1})
            except Exception: ok = False
        print("selftest", "ok" if ok else "failed"); return 0 if ok else 1
    os.makedirs(DIR, exist_ok=True)
    rp = os.path.join(DIR, "sent.json")
    results = json.load(open(rp)) if os.path.exists(rp) else {}
    before = json.dumps(results, sort_keys=True)
    failed = 0
    for path in sorted(glob.glob(os.path.join(DIR, "ed*-*.json"))):
        name = os.path.basename(path)[:-5]
        if name in results: continue                         # one post per request, ever
        try: req = json.load(open(path))
        except Exception: results[name] = {"state": "ERROR", "error": "unreadable-request", "posted_at_utc": None, "attempts": 0}; failed += 1; continue
        ok, why = check(name, req, results, edition_date(req.get("n")))
        if not ok: results[name] = {"state": "ERROR", "error": why, "posted_at_utc": None, "attempts": 0}; failed += 1; print(name, "refused:", why); continue
        if api is None: results[name] = {"state": "ERROR", "error": "login-failed", "posted_at_utc": None, "attempts": 0}; failed += 1; continue
        last = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                uri, existed = send(api, req)
                results[name] = {"state": "PUBLISHED", "uri": uri, "url": post_url(uri), "posted_at_utc": iso(), "attempts": attempt}
                if existed: results[name]["note"] = "already on the profile; not sent again"
                print(name, "published" + (" (was already there)" if existed else "")); last = None; break
            except Exception as e:
                last = err_word(e); print(name, "attempt", attempt, "failed:", last); time.sleep(20 * attempt)
        if last is not None:
            results[name] = {"state": "ERROR", "error": last, "posted_at_utc": None, "attempts": MAX_ATTEMPTS}; failed += 1
    if json.dumps(results, sort_keys=True) != before:
        json.dump(results, open(rp, "w"), indent=1, ensure_ascii=False); open(rp, "a").write("\n")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
