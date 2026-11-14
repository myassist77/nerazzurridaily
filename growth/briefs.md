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
- Does: a page per fixture, player and transfer-tracker pages, pages for queries Search Console already shows, internal links, index watch.
- Status: building. Started Nov 14 (/results/, /injuries/, US TV guide, /fixtures/ upgrade; index watch task running).
- Priority 1.

## Conversion
- Owns: signups per 100 real visits.
- Does: a signup form on every landing page, one test a week, welcome emails, double opt-in loss check.
- Status: building. Priority 1.

## Distribution
- Owns: real visits per channel.
- Does: daily video (running, do not re-engineer); daily link post on each tappable channel; matchday posts.
- Status: waiting on the owner creating Bluesky, Threads and Facebook Page accounts and signing each in to Postiz; and on the TikTok Business switch.

## Partnerships
- Owns: placements won per week.
- Does: Inter Clubs abroad, English-language creators, podcasts, newsletter swaps. One pitch, one follow-up.
- Status: waiting on one thing: the MAIL_PASSWORD repository secret (owner enters it once). Route chosen Nov 14, 2026: the outreach workflow sends through the Hostinger mailbox and reads replies.
- How: write the full message list to growth/outreach/queue.enc (Fernet, key in the private Drive file nerazzurri-outreach-key.txt), each item {id, to, to_name, subject, body, kind: pitch|followup, not_before?}. The workflow enforces: two messages per address at most, follow-up 5+ days after the pitch and only without a reply, 10 a run, 20 a day, signed Support Team. Read growth/outreach/state.enc for what was sent and who replied; status.json has counts.

## Community
- Owns: replies and referral signups.
- Does: answers YouTube comments, reader replies, polls, Wednesday debate; later a refer-a-friend link.
- Status: building. Debate and comment tasks running.
