# tools/ — the daily build

Run from the repo root in the Composio remote sandbox (fresh each morning: `curl -sL https://github.com/myassist77/nerazzurridaily/archive/refs/heads/main.tar.gz | tar xz`).

| script | job |
|---|---|
| `nd_render.py data/edition-N.json` | JSON → `p/edition-N/index.html`, `build/email-N.html`, `build/edition-N.txt` |
| `nd_render.py --index` | rebuild `index.html` + `sitemap.xml` from `data/` |
| `nd_mast.py` | 640×350 masthead PNG under 7,000 bytes; fails the build on any spec breach |
| `nd_controls.py --n N` | Playwright: overflow, contrast, type floor, masthead scale; screenshots + reviewer crops |
| `nd_checks.py` | text controls (American English, times, glosses, length, links); see the skill |
| `nd_publish.py` | workbench-only: one GitHub commit, one Brevo DRAFT |
| `nd_extract.py` / `nd_legacy_restyle.py` | one-time migration helpers (Sept 19, 2026) |

`build/` is scratch and is never committed. Editions 1–9 predate the JSON schema and live as HTML only (`data/legacy.json` lists them for the index).
