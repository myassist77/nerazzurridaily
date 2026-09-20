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
| `nd_social_publish.py` | workbench-only: upload the daily Short to YouTube (unlisted), set its 16:9 thumbnail, post the comment, flip it public; reads/writes `data/social-ed{N}.json` |
| `social_motion.py` | the motion-short renderer (1080×1920, 30 fps, silent): beats JSON → Playwright frames → ffmpeg MP4 + 9:16/16:9 thumbnails. Canonical copy; the nerazzurri-shorts skill's embedded copy is a fallback |
| `nd_extract.py` / `nd_legacy_restyle.py` | one-time migration helpers (Sept 19, 2026) |

`build/` is scratch and is never committed. Editions 1–9 predate the JSON schema and live as HTML only (`data/legacy.json` lists them for the index).

## Analytics (Cloudflare Web Analytics, since Sept 20, 2026)

The beacon is part of the shared `FONTS` head constant in `nd_render.py`, so every edition page and every index rebuild carries it automatically. Two guards keep it that way:

- `nd_render.py` refuses to write a web page without the beacon, and refuses to write an email that contains it (mail clients strip scripts).
- `.github/workflows/analytics-beacon.yml` runs `tools/check_beacon.py` on every push and fails if any HTML page — including the hand-edited `subscribe/`, `yt/` and `404.html` — has lost it. When hand-editing one of those pages, keep the `<!-- Cloudflare Web Analytics -->` snippet in its `<head>`.

## The Short (YouTube, automated since Sept 21, 2026)

The 6:45 AM social run renders the MP4 in the Composio workbench, commits it to
`assets/video/ed{N}.mp4`, uploads it to the channel **unlisted**, sets the 16:9 thumbnail, posts
the pinned-comment text, and writes `data/social-ed{N}.json` with the video id. A second task at
9:00 AM ET reads that file and flips the video to public — the two hours in between are the
owner's veto window.

Facts the code depends on, all measured against the live channel on Sept 20, 2026:

- `YOUTUBE_UPLOAD_VIDEO` takes an S3 key, so the MP4 has to be rendered (or copied) inside the
  workbench and staged into `/mnt/files/` — `get_mount_file_s3_key()`. A file in the run's own
  sandbox cannot be uploaded.
- A comment on a **private** video returns 404 `videoNotFound`; on an **unlisted** one it posts
  fine. That is why the first write is unlisted, never private.
- `YOUTUBE_UPDATE_THUMBNAIL` needs a public URL — `get_mount_file_url()` on the staged PNG. 16:9
  only: the 9:16 Shorts thumbnail is YouTube Partner Program + Studio desktop, no API.
- Pinning a comment has no API on any platform. The comment is posted; pinning is one tap or not
  at all.
- An upload costs 1,600 of the channel's 10,000 daily quota units.
- TikTok is **not** automated: Composio's TikTok app has no usable client key, and TikTok's own
  API forces private-only posts until the developer app passes an audit (Sept 20, 2026).
