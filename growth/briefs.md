# Agent briefs

Edited only by the Growth Lead. Status: running | building | waiting.

## Growth Lead
- Owns: real subscribers per week.
- Runs: Mondays 12:17 PM ET, after the Scorekeeper.
- May alone: edit this folder; apply the five rules; from Dec 14, 2026 set weekly_autopost to false in data/social-switch.json if rule 1 is met for the Sunday long-form video.
- Status: running since Nov 16, 2026.

## Scorekeeper (Monday numbers task)
- Owns: a correct funnel per channel: reach, real visits, signups, confirmations.
- Takes no growth action. Status: running. To add: per-channel funnel table.

## Editor desk (5:30 edition task)
- Owns: open rate and click rate among real subscribers.
- Status: running. To add: subject-line test, forward-to-a-friend ask, reader survey.

## Search
- Owns: Google clicks per week.
- Running: /fixtures/, /results/, /injuries/, the US TV guide, and since Nov 14, 2026 one page per men's match under /match/ (kickoff in every US time zone, US TV, form, injuries, result once played). All rebuilt by the edition workflow every morning from the edition data; nothing is written by hand.
- Weekly review task (Thursdays): reads Search Console, logs which pages and queries moved, proposes the next page type. It does not change code.
- Status: running. Priority 1.

## Conversion
- Owns: signups per 100 real visits.
- Running since Nov 14, 2026: every page already carries the signup form; each signup is now counted (one view of /subscribe/sent/ = one signup sent, its referrer = the page it came from; /subscribe/confirmed/ = one confirmation).
- Weekly headline or offer tests are NOT running: at about 12 real visits a week a test cannot show anything. The Lead starts them when real visits pass 200 a week for two weeks.
- Status: measuring. Tests waiting on traffic.

## Distribution
- Owns: real visits per channel.
- Running: the daily video on TikTok and YouTube (do not re-engineer). Since Nov 14, 2026 a daily link post on Bluesky (@nerazzurridaily.com (was @nerazzurridaily.bsky.social; the site file /.well-known/atproto-did proves the domain — never delete it or _config.yml)) through Postiz: the edition's title, one line and the door link /go/bsky/?ed=N, with the masthead image. The same task posts to Threads (door /go/th/) and the Facebook Page (door /go/fb/) as soon as those channels appear in Postiz. Record per edition: data/links/posted-edN.json. Switch: "links_autopost" in data/social-switch.json (missing = on).
- Status: Bluesky and the Facebook Page (facebook.com/nerazzurridaily) running. Threads and Instagram: skipped by the owner on Nov 14, 2026 (Threads only signs in through Instagram, and the Instagram username was already taken and not publicly visible). Do not list them as a blocker. The task would still post to Threads if the channel ever appears in Postiz. TikTok Business switch (the tappable bio link): the owner chose on Nov 14, 2026 to skip it for now; the bio keeps the typed address. Do not list it as a blocker; mention it again only if TikTok door visits become the best source.

## Partnerships
- Owns: placements won per week.
- Does: Inter Clubs abroad, English-language creators, podcasts, newsletter swaps. One pitch, one follow-up.
- Status: ready. The mailbox password secret is in place and the workflow's self-test passed on Nov 14, 2026 (23:10 UTC). No blocker. Nothing has been sent yet: the first pitches are queued by the Tuesday Nov 17 run and leave at the workflow's next run after that. Route: the outreach workflow sends through the Hostinger mailbox and reads replies.
- How: write the full message list to growth/outreach/queue.enc (Fernet, key in the private Drive file nerazzurri-outreach-key.txt), each item {id, to, to_name, subject, body, kind: pitch|followup, not_before?}. The workflow enforces: two messages per address at most, follow-up 5+ days after the pitch and only without a reply, 10 a run, 20 a day, signed Support Team. Read growth/outreach/state.enc for what was sent and who replied; status.json has counts.
- Owed mentions: add {"date", "name", "url", "text"} to data/mentions.json (public). The renderer prints it in that date's edition, page and email, as "From our friends."

## Community
- Owns: replies and referral signups.
- Running since Nov 15, 2026: a task (11:23 AM and 5:23 PM ET) answers every viewer who comments under our own YouTube videos, as the channel. Facts only from the edition data, with the edition's confirmed or reported label; an opinion gets an answer and a question back; the newsletter is named only when it answers what the viewer asked. At most 8 replies a run, three of ours per thread. A claimed mistake, a business or press request or a legal complaint is flagged to the owner, not answered. Record: growth/community/replies.jsonl (ids only, no text, no names). On Mondays it adds one ledger line with the week's counts.
- Also running: the daily question comment and the Wednesday debate (other tasks).
- Bluesky (owner's choice Nov 14, 2026: answer only people who reply to, mention or quote us): built, waiting on the app password. The workflow bluesky.yml (every three hours, and at once when the queue is committed) reads who wrote to us into the encrypted growth/community/bsky-state.enc and sends the answers the Community task queues in bsky-queue.enc. tools/nd_bsky.py refuses any reply to a post that was not addressed to us, a second answer to the same post, more than three answers to one person in a thread, a link to another site, and never likes, reposts, follows or messages. Counts only in growth/community/bsky-status.json. Replying to strangers' posts stays off: Bluesky asks automated accounts not to.
- Later: reader replies by email, a refer-a-friend link.
- Status: YouTube running (first run Nov 15, 2026; its read and reply calls were not testable the evening it was built, the YouTube quota was spent). Bluesky: waiting on the owner to store the repo secret BLUESKY_APP_PASSWORD; the workflow self-test ran green without it and reports waiting_for_password.
