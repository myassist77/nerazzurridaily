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
| `social_motion.py` | the motion-short renderer (1080×1920, 30 fps, run with --silent): beats JSON → Playwright frames → ffmpeg MP4 + 9:16/16:9 thumbnails. Canonical copy; the nerazzurri-shorts skill's embedded copy is a fallback. Since Nov 15, 2026 the foot of every beat reads "FREE DAILY EMAIL · nerazzurridaily.com" (constant `FOOT`), not the bare address, so a viewer who never reaches the end card still sees what the address is for |
| `nd_voice.py` | the voiceover (since Sept 26, 2026): `plan` speaks each beat's `"vo"` line (Kokoro, voice am_michael; `[bracketed]` Italian names in Italian) and times the beats to it; `mix` lays the voice on the silent render at -16 LUFS, 48 kHz stereo AAC, and with `--cover` opens on the 9:16 thumbnail for 1.0 s (was 0.2 s until Sept 29, 2026) so it is the TikTok cover; that makes the voiced ceiling 39.0 s. Voice only, no music |
| `nd_extract.py` / `nd_legacy_restyle.py` | one-time migration helpers (Sept 19, 2026) |

`build/` is scratch and is never committed. Editions 1–9 predate the JSON schema and live as HTML only (`data/legacy.json` lists them for the index).

## Analytics (Cloudflare Web Analytics, since Sept 20, 2026)

The beacon is part of the shared `FONTS` head constant in `nd_render.py`, so every edition page and every index rebuild carries it automatically. Two guards keep it that way:

- `nd_render.py` refuses to write a web page without the beacon, and refuses to write an email that contains it (mail clients strip scripts).
- `.github/workflows/analytics-beacon.yml` runs `tools/check_beacon.py` on every push and fails if any HTML page — including the hand-edited `subscribe/`, `yt/` and `404.html` — has lost it. When hand-editing one of those pages, keep the `<!-- Cloudflare Web Analytics -->` snippet in its `<head>`.

## The Short — TikTok + YouTube through Postiz (since Sept 26, 2026)

1. **6:45 AM ET** social task renders the six-beat MP4 (voice only since Sept 26, 2026: `nd_voice.py plan` → `social_motion.py --silent` → `nd_voice.py mix --cover`) and commits
   `assets/video/ed{N}.mp4`, `assets/video/ed{N}-thumb-9x16.png` (9:16, the YouTube thumbnail since Sept 29, 2026),
   `assets/video/ed{N}-thumb.png` (16:9 fallback), `data/tiktok-ed{N}.json`
   (title, caption) and `data/youtube-ed{N}.json` (title, description, tags, comment). It posts nothing.
2. **7:30 AM ET** Postiz task (`CRON_TZ=America/New_York`; moved from 9:05 on Nov 14, 2026 — if the post files are not committed yet it re-checks every 15 minutes until 9:15 AM ET) uploads the MP4 to Postiz by URL from the
   live site and posts it — TikTok (DIRECT_POST, public, voiced) and YouTube (public, title,
   description, tags, 9:16 thumbnail — 16:9 if the 9:16 is missing — comment). 6:45 → 7:30 is the owner's veto window.
   The owner can end the window early by running the 7:30 task by hand (Run now) any time after the 6:45
   task has committed; the scheduled 7:30 run then finds the post record and stops silently.
3. It records what it posted in `data/posted-ed{N}.json` **before** verifying (the primary
   never-post-twice guard — Postiz's post list has come back empty while posts existed), then
   fills in the real states and the YouTube video id. The Monday numbers task reads these files.
4. Matchday full-time cards follow the same route immediately after the whistle: media at
   `assets/video/ft-{date}.mp4`, record at `data/posted-ft-{date}.json`.

Kill switches: `data/social-switch.json` — `tiktok_autopost`, `youtube_autopost` (missing = on).
Old files `data/social-ed{N}.json` (Sept 20–25) are the retired direct-upload era, kept for history.

Facts that still hold:

- Pinning a comment has no API on any platform. A 16:9 custom thumbnail sent through the API is applied
  (checked Sept 29, 2026 on No. 28), but the Shorts shelf showed a YouTube-picked frame; since Sept 29 the
  post task (9:05, now 7:30) sends the 9:16 image and reports whether the Shorts shelf (oar2.jpg) actually shows it.
- Postiz posts cannot be deleted through its tools, and its "draft" type is unreliable for TikTok —
  never create drafts.
- No API attaches a trending sound; the only sound is the voiceover baked into the MP4 (no music — the generated soundtrack was rejected Sept 26, 2026).
- Postiz has no TikTok cover setting; TikTok uses the opening frame, which `nd_voice.py mix --cover` makes the designed 9:16 thumbnail (held 1.0 s).
- Neither TikTok's API nor Postiz can post a TikTok Story (checked Sept 29, 2026); the owner dropped the idea.

## Evergreen search pages (`nd_evergreen.py`, added Nov 14, 2026)

`nd_render.py --index` now also calls `tools/nd_evergreen.py`, which writes three pages and rebuilds `/fixtures/` with
structured data: `/results/` (every result the editions have carried), `/injuries/` (every edition item about an injury,
confirmed kept apart from reported) and `/how-to-watch-inter-milan-in-the-usa/` (the US listing for every match).
Every fact on them is read from `data/edition-*.json`; nothing is written by hand. The layer is fenced off from the
morning build: `nd_render.py` calls it inside `try/except` and keeps its own `/fixtures/` page if anything fails, and
`edition.yml` commits the three pages only when they exist. The sitemap lists them, the footers link to them, and
`check_signup_form.py` tests the form on each. Run it alone from the repo root with `python3 tools/nd_evergreen.py`.

## Site header and navigation (added Nov 14, 2026)

`nd_render.py` has two headers. `masthead(here)` is the tall block on the home page and the four reference pages
(`/fixtures/`, `/results/`, `/injuries/`, `/how-to-watch-inter-milan-in-the-usa/`): the eyebrow line, the wordmark in
Anton (the masthead image's own face), the kit stripes on the right edge, a "Get it free" link to the page's form, and
`nav(here)` inside it. Edition pages, `/subscribe/` and the `/go/` doors keep the slim `.top` bar, now with the Anton
wordmark and a stripe end-cap; edition pages also carry the light `nav()` strip under it, while `/subscribe/` and the
doors stay bare on purpose (landing pages with one job). On phones the last nav link reads "US TV" so the five links
fit one line. Page text keeps the 13px floor. Editions before No. 74 keep the header they were built with: an edition
page is rendered once, on its morning.

## Rebuilding every edition page (Nov 14, 2026)

A change to the header, the navigation, the footer or the page CSS reaches a new edition on its own, but an edition that is
already published keeps the page it was built with. `.github/workflows/rebuild-pages.yml` (run by hand: Actions → rebuild-pages,
or a `workflow_dispatch` on `rebuild-pages.yml`) brings them all up to date in one commit:

1. it re-renders every `data/edition-N.json` with `nd_render.py` (only `p/edition-N/index.html` is kept; `build/` is scratch,
   and no masthead, email, index page, feed or sitemap is touched);
2. it runs `nd_legacy_forms.py`, whose header step gives editions No. 1–9 (HTML only) the same top bar, navigation strip
   and footer links from the renderer's own `NAV_CSS`, `HEAD_CSS` and `nav()`;
3. it checks every edition page (one top bar, one navigation strip, one signup form, the current fonts, the beacon) and runs
   `check_beacon.py` and `check_signup_form.py`; it commits only when all of that passes, and commits nothing otherwise.

It also rewrites `404.html` (`python3 tools/nd_evergreen.py --404`): the "Page not found" page carries the same header,
navigation, signup form and footer as the reference pages since Nov 14, 2026, and is no longer edited by hand.

It shares the `edition` workflow's concurrency group, so it never runs alongside a morning build. A push by a workflow does
not start the other workflows: dispatch `signup-form.yml` afterwards if you want its run on the new commit.

## Growth team tools (added Nov 14-15, 2026)

- `nd_mail.py` with `.github/workflows/outreach.yml`: sends the partner outreach queue through the site mailbox and reads replies (14:23 and 21:23 UTC). Partner data lives only in the encrypted `growth/outreach/*.enc` files. Rules are in the file's docstring.
- `nd_social_brand.py`: draws the profile picture and the Bluesky and Facebook covers into `assets/brand/`.
- `nd_evergreen.py` also builds one page per match under `/match/`.
- `data/mentions.json`: partner mentions printed as "From our friends." in that date's edition. An empty list changes nothing.
- `/subscribe/sent/`: loaded in a hidden frame when a signup goes through, so signups can be counted. `check_signup_form.py` fails unless it is requested exactly once.
- `.well-known/atproto-did` and `_config.yml`: prove the domain for the Bluesky handle @nerazzurridaily.com. Never delete either.
- `nd_bsky.py` with `.github/workflows/bluesky.yml`: answers people who reply to, mention or quote us on Bluesky, and nobody else (every three hours, and when `growth/community/bsky-queue.enc` is committed). Needs the repo secret `BLUESKY_APP_PASSWORD`. Rules are in the file's docstring; who wrote and what was said live only in the encrypted `growth/community/bsky-*.enc` files.
- `nd_bsky_post.py` with `.github/workflows/bluesky-post.yml`: publishes our own Bluesky posts (the daily link post and the daily question) since Nov 15, 2026, when Postiz lost its Bluesky sign-in. A task commits a request `data/links/bsky/ed<N>-<kind>.json` (`{n, kind, text, image, alt}`); the workflow posts it with the same `BLUESKY_APP_PASSWORD` secret, reads the post back, and writes `data/links/bsky/sent.json`. Only `PUBLISHED` there means it is live. One post per request file, ever; to resend a failed one, remove its entry from `sent.json` and re-run the workflow. Bluesky is no longer posted through Postiz.
- `nd_growth_captions.py`: the Facebook and Bluesky words for the day's video (since Nov 15, 2026 the 7:43 AM task posts the video there, with a plain link post as the fallback). Built only from `data/tiktok-edN.json` plus fixed lines, so nothing is invented; it fails on a caption it cannot clean with certainty and the task then sends the link post. Facebook: the caption has no link, the link is the first comment (door `/go/fb/?ed=N&v=reel`). Bluesky: video + tappable link (door `/go/bsky/?ed=N&v=video`) + the day's hashtags (three when they fit, else two: tags are how Bluesky's topic feeds and tag searches find a post); `nd_bsky_post.py` uploads the video through Bluesky's video service. Off switch: `"video_on_facebook_bluesky": false` in `data/social-switch.json`.
  Two more modes since Nov 15, 2026. `--ft <date>`: the same for the FULL-TIME card of a match (from `data/tiktok-ft-<date>.json`; doors `/go/fb/?ed=N&v=ft` and `/go/bsky/?ed=N&v=ft`, both landing on `/subscribe/`), used by the full-time task that puts the card on Facebook and Bluesky after the one-shot has put it on TikTok and YouTube; the Bluesky request is `data/links/bsky/ed<N>-ft.json`, kind `ft`. Off switch: `"fulltime_on_facebook_bluesky": false`. `--question <N>`: the Bluesky text of the day's question (from `data/youtube-edN.json`, plus the edition link and the day's hashtags), used by the 12:07 PM question task.
- Weekly builds: `growth/build-queue.md`. A page type added to `PATHS` and `RENDERERS` in `nd_evergreen.py` is built inside a try and listed in `build/evergreen-paths.txt`; the edition workflow commits `<folder>/index.html` for every line of that file, so a new page type needs no workflow change.
- `prompts/fulltime-card.txt`: the full-time card's instructions, moved out of the 5:30 edition prompt on Nov 14, 2026 (that prompt had passed the 65,536-byte limit for scheduled tasks). The edition task copies it into the matchday one-shot it schedules and first checks the file's sha256 against the value written in its own prompt. NEVER edit this file without updating that value in the 5:30 prompt in the same session: on a mismatch the full-time card is not scheduled.
- Team memory and rules: `growth/README.md`.
