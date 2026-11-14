#!/usr/bin/env python3
"""nd_mail.py - partner outreach through the site's own Hostinger mailbox.

Runs only inside .github/workflows/outreach.yml. The repo is public, so the queue,
the sent record and the replies are kept ENCRYPTED (Fernet, secret OUTREACH_KEY):
  growth/outreach/queue.enc   written by the Partnerships agent
  growth/outreach/state.enc   written here (sent record, replies, last inbox uid)
  growth/outreach/status.json written here, counts only, no addresses
Never print an address, a subject or a body: the run log is public.

Modes: selftest | send | check | all (send then check).
Rules enforced here, whatever the queue says:
  - at most 2 messages ever to one address (one pitch, one follow-up)
  - a follow-up only 5+ days after its pitch and only if that address has not written back
  - at most MAX_PER_RUN sends a run and MAX_PER_DAY a day
  - the body must be signed "Nerazzurri Daily Support Team" and must not name the owner
"""
import os, sys, json, ssl, time, smtplib, imaplib, email, email.utils, email.policy, datetime as dt
from email.message import EmailMessage
from email.header import decode_header, make_header
from cryptography.fernet import Fernet

ADDR = os.environ.get("MAIL_ADDRESS", "mail@nerazzurridaily.com")
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.hostinger.com")
IMAP_HOST = os.environ.get("IMAP_HOST", "imap.hostinger.com")
PASSWORD = os.environ.get("MAIL_PASSWORD", "")
KEY = os.environ.get("OUTREACH_KEY", "")
DRY = os.environ.get("DRY_RUN") == "1"
DIR = os.environ.get("OUTREACH_DIR", "growth/outreach")
MAX_PER_RUN, MAX_PER_DAY, FOLLOWUP_DAYS = 10, 20, 5
SIGN = "Nerazzurri Daily Support Team"
BANNED = ("macrina",)

def now(): return dt.datetime.now(dt.timezone.utc)
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

def status(**kw):
    os.makedirs(DIR, exist_ok=True)
    p = os.path.join(DIR, "status.json")
    old = json.load(open(p)) if os.path.exists(p) else {}
    old.update(kw); old["last_run_utc"] = now().strftime("%Y-%m-%dT%H:%M:%SZ")
    json.dump(old, open(p, "w"), indent=1); open(p, "a").write("\n")

def norm(a): return (email.utils.parseaddr(a or "")[1] or "").strip().lower()

def allowed(item, state):
    """Return (ok, reason). Reasons are generic words, safe for the public log."""
    to = norm(item.get("to")); body = item.get("body") or ""; kind = item.get("kind")
    if not item.get("id") or not to or "@" not in to or not item.get("subject") or not body: return False, "incomplete"
    if kind not in ("pitch", "followup"): return False, "bad-kind"
    if item["id"] in state["sent"]: return False, "already-sent"
    if SIGN not in body: return False, "unsigned"
    low = (body + " " + item["subject"]).lower()
    if any(b in low for b in BANNED): return False, "names-owner"
    if to == ADDR.lower(): return False, "self"
    prior = [s for s in state["sent"].values() if s["to"] == to]
    if len(prior) >= 2: return False, "limit-two"
    replied = any(r.get("from") == to for r in state["replies"])
    if kind == "pitch" and prior: return False, "already-pitched"
    if kind == "followup":
        if not prior: return False, "no-pitch"
        if replied: return False, "they-replied"
        age = (now() - dt.datetime.fromisoformat(prior[0]["date"])).days
        if age < FOLLOWUP_DAYS: return False, "too-soon"
    nb = item.get("not_before")
    if nb and today() < nb: return False, "not-yet"
    return True, "ok"

def build(item, state):
    m = EmailMessage()
    m["From"] = email.utils.formataddr(("Nerazzurri Daily", ADDR))
    m["To"] = email.utils.formataddr((item.get("to_name") or "", norm(item["to"])))
    m["Subject"] = item["subject"]
    m["Date"] = email.utils.formatdate(localtime=False)
    m["Message-ID"] = email.utils.make_msgid(domain=ADDR.split("@")[1])
    if item["kind"] == "followup":
        prior = [s for s in state["sent"].values() if s["to"] == norm(item["to"])]
        if prior and prior[0].get("message_id"):
            m["In-Reply-To"] = prior[0]["message_id"]; m["References"] = prior[0]["message_id"]
    m.set_content(item["body"])
    return m

def imap():
    c = imaplib.IMAP4_SSL(IMAP_HOST, 993, ssl_context=ssl.create_default_context())
    c.login(ADDR, PASSWORD); return c

def file_sent(c, msg):
    for box in ("INBOX.Sent", "Sent", "Sent Items", "Sent Messages"):
        try:
            typ, _ = c.append(box, "(\\Seen)", imaplib.Time2Internaldate(time.time()), msg.as_bytes())
            if typ == "OK": return True
        except Exception: pass
    return False

def do_send(state):
    queue = load("queue.enc", [])
    sent_today = sum(1 for s in state["sent"].values() if s["date"][:10] == today())
    done, skipped = 0, {}
    smtp = c = None
    for item in queue:
        if done >= MAX_PER_RUN or sent_today + done >= MAX_PER_DAY: break
        ok, why = allowed(item, state)
        if not ok:
            if why != "already-sent": skipped[why] = skipped.get(why, 0) + 1
            continue
        msg = build(item, state)
        if not DRY:
            if smtp is None:
                smtp = smtplib.SMTP_SSL(SMTP_HOST, 465, context=ssl.create_default_context(), timeout=60)
                smtp.login(ADDR, PASSWORD); c = imap()
            smtp.send_message(msg); file_sent(c, msg); time.sleep(20)
        state["sent"][item["id"]] = {"to": norm(item["to"]), "kind": item["kind"], "date": now().isoformat(), "message_id": msg["Message-ID"]}
        done += 1; save("state.enc", state)
    if smtp: smtp.quit()
    if c: c.logout()
    print("sent", done, "skipped", json.dumps(skipped))
    return done, skipped

def text_of(m):
    part = m.get_body(preferencelist=("plain", "html")) if hasattr(m, "get_body") else None
    try: return (part.get_content() if part else "")[:3000]
    except Exception: return ""

def do_check(state):
    c = imap(); c.select("INBOX", readonly=True)
    last = int(state.get("last_uid", 0))
    typ, data = c.uid("search", None, "UID", "%d:*" % (last + 1))
    uids = [int(u) for u in (data[0] or b"").split() if int(u) > last]
    sent_ids = {s["message_id"]: k for k, s in state["sent"].items() if s.get("message_id")}
    sent_to = {s["to"]: k for k, s in state["sent"].items()}
    new = 0
    for u in uids[-200:]:
        typ, d = c.uid("fetch", str(u), "(BODY.PEEK[])")
        if typ != "OK" or not d or not d[0]: continue
        m = email.message_from_bytes(d[0][1], policy=email.policy.default)
        frm = norm(m.get("From"))
        if frm == ADDR.lower(): continue
        refs = (m.get("In-Reply-To") or "") + " " + (m.get("References") or "")
        match = next((k for mid, k in sent_ids.items() if mid in refs), None) or sent_to.get(frm)
        state["replies"].append({"uid": u, "date": m.get("Date"), "from": frm, "from_name": email.utils.parseaddr(m.get("From") or "")[0],
            "subject": str(make_header(decode_header(m.get("Subject") or ""))), "matched_id": match,
            "auto": bool(m.get("Auto-Submitted") and m.get("Auto-Submitted") != "no"), "text": text_of(m)})
        new += 1
    if uids: state["last_uid"] = max(uids)
    state["replies"] = state["replies"][-400:]
    c.logout(); save("state.enc", state)
    print("new inbound", new)
    return new

def selftest():
    msg = EmailMessage()
    msg["From"] = email.utils.formataddr(("Nerazzurri Daily", ADDR)); msg["To"] = ADDR
    msg["Subject"] = "Nerazzurri Daily mail route test " + now().strftime("%Y-%m-%d %H:%M UTC")
    msg["Message-ID"] = email.utils.make_msgid(domain=ADDR.split("@")[1]); msg["Date"] = email.utils.formatdate()
    msg.set_content("Automated test of the outreach mail route. Nothing to do.\n\n" + SIGN)
    s = smtplib.SMTP_SSL(SMTP_HOST, 465, context=ssl.create_default_context(), timeout=60)
    s.login(ADDR, PASSWORD); s.send_message(msg); s.quit()
    c = imap(); filed = file_sent(c, msg); found = False
    for _ in range(9):
        time.sleep(10); c.select("INBOX", readonly=True)
        typ, d = c.search(None, "HEADER", "Message-ID", msg["Message-ID"])
        if typ == "OK" and d[0].split(): found = True; break
    c.logout()
    print("selftest smtp ok, filed in Sent:", filed, "arrived in inbox:", found)
    return found

def main():
    mode = (sys.argv[1] if len(sys.argv) > 1 else "all").strip()
    if not KEY: print("OUTREACH_KEY missing"); sys.exit(1)
    if not PASSWORD and not DRY:
        print("mail password secret not set - nothing sent, nothing read")
        status(mode=mode, waiting_for_password=True); return
    state = load("state.enc", {}); state.setdefault("sent", {}); state.setdefault("replies", []); state.setdefault("last_uid", 0)
    st = {"mode": mode, "waiting_for_password": False, "error": None}
    try:
        if mode == "selftest": st["selftest_ok"] = selftest(); st["selftest_utc"] = now().strftime("%Y-%m-%dT%H:%M:%SZ")
        if mode in ("send", "all"): st["sent_this_run"], st["skipped_this_run"] = do_send(state)
        if mode in ("check", "all") and not DRY: st["new_inbound_this_run"] = do_check(state)
    except Exception as ex:
        st["error"] = type(ex).__name__; print("error:", type(ex).__name__)
        save("state.enc", state); status(**st, sent_total=len(state["sent"]), inbound_total=len(state["replies"])); sys.exit(1)
    status(**st, sent_total=len(state["sent"]), inbound_total=len(state["replies"]))

if __name__ == "__main__":
    main()
