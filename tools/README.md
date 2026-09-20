# tools/ — the daily build

Run from the repo root in the Composio remote sandbox (fresh each morning: `curl -sL https://github.com/myassist77/nerazzurridaily/archive/refs/heads/main.tar.gz | tar xz`).

| script | job |
|---|---|
| `nd_render.py data/edition-N.json` | JSON → `p/edition-N/index.html`, `build/email-N.html`, `build/edition-N.txt` |
| `nd_render.py --index` | rebuild `index.html` + `sitemap.xml` from `data/` |
| `nd_mast.py` | 640×350 masthead PNG under 7,000 bytes; fails the build on any spec breach |
| `nd_controls.py --n N` | Playwright: overflow, contrast, type floor, masthead scale; screenshots + reviewer crops |
| `nd_checks.py` | text controls (American English, times, glosses, length, links); see the skill |
| `check_beacon.py` | fails if any repo HTML page lacks the Cloudflare Web Analytics beacon (run by `.github/workflows/analytics-beacon.yml` on every push) |
| `nd_publish.py` | workbench-only: one GitHub commit, one Brevo DRAFT |
| `nd_extract.py` / `nd_legacy_restyle.py` | one-time migration helpers (Sept 19, 2026) |

`build/` is scratch and is never committed. Editions 1–9 predate the JSON schema and live as HTML only (`data/legacy.json` lists them for the index).

## Analytics (Cloudflare Web Analytics, since Sept 20, 2026)

The beacon is part of the shared `FONTS` head constant in `nd_render.py`, so every edition page and every index rebuild carries it automatically. Two guards keep it that way:

- `nd_render.py` refuses to write a web page without the beacon, and refuses to write an email that contains it (mail clients strip scripts).
- `.github/workflows/analytics-beacon.yml` runs `tools/check_beacon.py` on every push and fails if any HTML page — including the hand-edited `subscribe/`, `yt/` and `404.html` — has lost it. When hand-editing one of those pages, keep the `<!-- Cloudflare Web Analytics -->` snippet in its `<head>`.
