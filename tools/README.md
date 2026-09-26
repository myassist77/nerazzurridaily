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
| `nd_social_publish.py` | RETIRED for posting since Sept 26, 2026 (YouTube now goes through Postiz). Kept for read helpers (`yt_status`) and the legacy `data/social-ed{N}.json` files |
| `social_motion.py` | the motion-short renderer (1080×1920, 30 fps, silent): beats JSON → Playwright frames → ffmpeg MP4 + 9:16/16:9 thumbnails. Canonical copy; the nerazzurri-shorts skill's embedded copy is a fallback |
| `nd_extract.py` / `nd_legacy_restyle.py` | one-time migration helpers (Sept 19, 2026) |

`build/` is scratch and is never committed. Editions 1–9 predate the JSON schema and live as HTML only (`data/legacy.json` lists them for the index).

## Analytics (Cloudflare Web Analytics, since Sept 20, 2026)

The beacon is part of the shared `FONTS` head constant in `nd_render.py`, so every edition page and every index rebuild carries it automatically. Two guards keep it that way:

- `nd_render.py` refuses to write a web page without the beacon, and refuses to write an email that contains it (mail clients strip scripts).
- `.github/workflows/analytics-beacon.yml` runs `tools/check_beacon.py` on every push and fails if any HTML page — including the hand-edited `subscribe/`, `yt/` and `404.html` — has lost it. When hand-editing one of those pages, keep the `<!-- Cloudflare Web Analytics -->` snippet in its `<head>`.

## The Short — TikTok + YouTube through Postiz (since Sept 26, 2026)

1. **6:45 AM ET** social task renders the silent MP4 in the Composio workbench and commits
   `assets/video/ed{N}.mp4`, `assets/video/ed{N}-thumb.png` (16:9), `data/tiktok-ed{N}.json`
   (title, caption) and `data/youtube-ed{N}.json` (title, description, tags, comment). It posts nothing.
2. **9:05 AM ET** Postiz task (`CRON_TZ=America/New_York`) uploads the MP4 to Postiz by URL from the
   live site and posts it — TikTok (DIRECT_POST, public, silent) and YouTube (public, title,
   description, tags, 16:9 thumbnail, comment). 6:45 → 9:05 is the owner's veto window.
3. It records what it posted in `data/posted-ed{N}.json` **before** verifying (the primary
   never-post-twice guard — Postiz's post list has come back empty while posts existed), then
   fills in the real states and the YouTube video id. The Monday numbers task reads these files.
4. Matchday full-time cards follow the same route immediately after the whistle: media at
   `assets/video/ft-{date}.mp4`, record at `data/posted-ft-{date}.json`.

Kill switches: `data/social-switch.json` — `tiktok_autopost`, `youtube_autopost` (missing = on).
Old files `data/social-ed{N}.json` (Sept 20–25) are the retired direct-upload era, kept for history.

Facts that still hold:

- Pinning a comment has no API on any platform; the 9:16 Shorts thumbnail is Studio-desktop only.
- Postiz posts cannot be deleted through its tools, and its "draft" type is unreliable for TikTok —
  never create drafts.
- A machine-posted TikTok is silent: no API attaches a trending sound (owner accepted this Sept 25, 2026).
