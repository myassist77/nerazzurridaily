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
- Already in every edition (checked Nov 14, 2026): a "reply with one word" ask that says every reply is read, and a forward-to-a-friend line with its own door (/go/forward/). The welcome email (sent by Brevo on the confirm click) asks where the reader is from, also by reply.
- Since Nov 15, 2026 each email also ends with a one-tap question: "Was today worth your 90 seconds? Yes · Not today" (door /go/vote/, landing on /thanks/). Counting is described in growth/README.md.
- Reader replies are now read and answered by the Community agent (see Community).
- Status: running. To add: subject-line test, reader survey.

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
- Since Nov 15, 2026 it also starts one conversation a day: at 12:07 PM ET a task posts the day's question (the same one the YouTube Short asks, copied word for word from data/youtube-edN.json) on our own Bluesky account and Facebook Page. Record: data/links/question-edN.json. Switch: "question_autopost" in data/social-switch.json (missing = on). Replies on Bluesky reach the answers task; comments on the Facebook Page are NOT read by any agent yet.
- Also running: the daily question comment on YouTube and the Wednesday debate (other tasks).
- Bluesky (owner's choice Nov 14, 2026: answer only people who reply to, mention or quote us): running. The workflow bluesky.yml (every three hours, and at once when the queue is committed) reads who wrote to us into the encrypted growth/community/bsky-state.enc and sends the answers the Community task queues in bsky-queue.enc. tools/nd_bsky.py refuses any reply to a post that was not addressed to us, a second answer to the same post, more than three answers to one person in a thread, a link to another site, and never likes, reposts, follows or messages. Counts only in growth/community/bsky-status.json. Replying to strangers' posts stays off: Bluesky asks automated accounts not to.
- Reader mail (since Nov 15, 2026): a task at 9:47 AM and 4:47 PM ET reads what readers wrote to the site mailbox (encrypted in growth/outreach/state.enc) and answers each person once, through the outreach workflow, kind "reader". The mail tool refuses a reader message to anyone who did not write first, to a partner address, or to a message older than 14 days. A claimed mistake, a business request or a legal complaint is flagged to the owner; an unsubscribe request is carried out in Brevo. What readers ask for, without names: growth/community/reader-notes.md.
- Later: a refer-a-friend link.
- Status: YouTube running (first run Nov 15, 2026; its read and reply calls were not testable the evening it was built, the YouTube quota was spent). Bluesky: running since Nov 15, 2026. The app password secret is in place, the self-test passed (login and notification read) and the first real read found nobody waiting. A real send has not happened yet; the first answer is the test.

## Builder and Reviewer (the weekly build, since Nov 15, 2026)
- Own: one useful build a week, live without the owner. Queue: growth/build-queue.md, first `ready` item first.
- Builder (Fridays 3:41 PM ET): builds one item on a branch named build/..., opens a pull request, never merges. May change only tools/nd_evergreen.py and new tools/nd_growth_*.py; at most 250 lines; facts from the edition data only.
- Reviewer (Saturdays and Tuesdays 1:19 PM ET): a separate agent that did not write it. Checks the files, the size, the automatic checks, the whole diff, rebuilds the site to confirm the edition pages are byte-identical, reads the new page; then merges or rejects. Never edits code.
- A merged build goes live with the next morning's edition (the edition workflow commits any page folder listed in build/evergreen-paths.txt). Undo = revert the one commit.
- Not theirs: the edition, the email, the videos, workflows, the navigation bar, scheduled tasks, money, passwords, accounts.
- Status: running. First build Fri Nov 20, 2026 (transfer news page); first review Sat Nov 21.
