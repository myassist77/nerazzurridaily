#!/usr/bin/env python3
"""Functional check: the Brevo signup form must actually submit.

Presence is not function. On 20 Sep 2026 the home page carried a complete-looking
form that sent nothing: the Subscribe button had been rebuilt without Brevo's
loader <svg>, main.js threw `removeClass of null` on submit, and every signup was
silently swallowed. This check drives the real page in headless Chromium, stubs
Brevo's endpoint (so no real subscriber is ever created), clicks Subscribe and
fails unless the POST is actually attempted and the success panel appears.

Usage:  python3 tools/check_signup_form.py [--pages index.html subscribe/index.html]
Needs:  pip install playwright && python3 -m playwright install --with-deps chromium
"""
import argparse, functools, http.server, re, socketserver, sys, threading, time

def _editions():
    """The newest JSON-rendered edition and the oldest legacy page: every edition page carries the form now."""
    import glob, os
    ns = sorted(int(re.search(r"edition-(\d+)", p).group(1)) for p in glob.glob("p/edition-*/index.html"))
    return [f"p/edition-{ns[-1]}/index.html", f"p/edition-{ns[0]}/index.html"] if ns else []

PAGES = ["index.html", "subscribe/index.html"] + _editions()
STUB = ('{"success":true,"message":"Almost there. Check your inbox for an email from '
        'Nerazzurri Daily and tap the confirm link."}')
TEST_EMAIL = "ci-check@example.invalid"   # never reaches Brevo: the POST is stubbed


def serve(root, port):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=root)
    socketserver.TCPServer.allow_reuse_address = True
    httpd = socketserver.TCPServer(("127.0.0.1", port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def check(page_path, base, browser):
    from playwright.sync_api import Error as PWError
    errors, posted = [], []
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.on("pageerror", lambda e: errors.append(str(e)))

    def route(r):
        posted.append(r.request.method)
        r.fulfill(status=200, content_type="application/json", body=STUB)

    # regex, not a glob: the host is <id>.sibforms.com and glob ** will not
    # split inside a host segment.
    page.route(re.compile(r"sibforms\.com/serve/"), route)
    url = f"{base}/{page_path}"
    page.goto(url, wait_until="networkidle", timeout=60000)

    problems = []
    if not page.is_visible("#EMAIL"):
        problems.append("no visible email field")
    if not page.is_visible("button[type=submit]"):
        problems.append("no visible submit button")
    if page.query_selector("button[type=submit] .sib-hide-loader-icon") is None:
        problems.append("Subscribe button is missing Brevo's loader <svg> "
                        "(main.js throws on submit and no signup is sent)")
    if problems:
        page.close()
        return problems

    page.fill("#EMAIL", TEST_EMAIL)
    page.click("button[type=submit]")
    try:
        page.wait_for_selector("#success-message:visible", timeout=15000)
    except PWError:
        problems.append("success message never appeared after submit")
    if not posted:
        problems.append("NO request was sent to Brevo — the form is dead")
    elif posted[0] != "POST":
        problems.append(f"expected POST to Brevo, saw {posted[0]}")
    if errors:
        problems.append("JavaScript error on submit: " + errors[0][:160])
    page.close()
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", nargs="*", default=PAGES)
    ap.add_argument("--root", default=".")
    ap.add_argument("--port", type=int, default=8731)
    ap.add_argument("--base", help="test a live origin instead of the local files")
    a = ap.parse_args()

    from playwright.sync_api import sync_playwright
    httpd = None
    base = a.base.rstrip("/") if a.base else None
    if not base:
        httpd = serve(a.root, a.port)
        base = f"http://127.0.0.1:{a.port}"
        time.sleep(0.4)

    failed = False
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for page_path in a.pages:
            target = page_path[:-len("index.html")] if page_path.endswith("index.html") else page_path
            problems = check(target if a.base else page_path, base, browser)
            if problems:
                failed = True
                print(f"FAIL  {page_path}")
                for pr in problems:
                    print(f"        - {pr}")
            else:
                print(f"ok    {page_path}  (POST attempted, success panel shown, no JS errors)")
        browser.close()
    if httpd:
        httpd.shutdown()
    if failed:
        print("\ncheck_signup_form: the signup form does not work. Refusing this build.")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
