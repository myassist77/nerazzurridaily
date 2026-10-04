#!/usr/bin/env python3
"""Fail if any published HTML page in the repo lacks the Cloudflare Web Analytics beacon.

Covers hand-edited pages (subscribe/, yt/, 404.html) as well as rendered ones.
build/ (scratch, incl. email HTML) and .git/ are skipped. Run from the repo root.
Exit 0 = every page carries the beacon; exit 1 = list of offending files.
"""
import os, re, sys

TOKEN = 'fd1d42426a934b7e94ed7cfe7afc9ccc'
SCRIPT = 'static.cloudflareinsights.com/beacon.min.js'
SKIP = {'.git', 'build', 'node_modules', '.github', 'templates'}
# Google Search Console verification files must stay byte-exact, so they never carry the beacon.
GSC_VERIFY = re.compile(r'google[0-9a-f]+\.html')

missing, checked = [], 0
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in SKIP]
    for f in files:
        if not f.endswith('.html'):
            continue
        p = os.path.join(root, f)[2:]
        if root == '.' and GSC_VERIFY.fullmatch(f):
            continue
        s = open(p, encoding='utf-8', errors='replace').read()
        checked += 1
        if SCRIPT not in s or TOKEN not in s:
            missing.append(p)

print(f'check_beacon: {checked} pages checked, {len(missing)} missing the beacon')
for p in sorted(missing):
    print(f'  MISSING: {p}')
sys.exit(1 if missing else 0)
