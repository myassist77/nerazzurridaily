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
- Since Nov 15, 2026 the edition task reads growth/community/reader-notes.md before it closes its research (what readers asked for in the last 7 days).
- The edition task's prompt was at the size limit for scheduled tasks (65,536 bytes) and could not be edited; the full-time card's instructions now live in tools/prompts/fulltime-card.txt, checked by hash before use. First matchday on the new route: Atalanta, Sun Nov 22, 2026.
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
- Route change, Nov 15, 2026 (owner's choice): Bluesky is NOT posted through Postiz any more. Postiz lost its Bluesky sign-in that morning and edition 75's link post failed while the record said PUBLISHED. Bluesky posts now go through the repo: the task commits data/links/bsky/ed<N>-link.json (or -question.json), the workflow bluesky-post.yml posts it with the repo's own app password, reads it back and writes data/links/bsky/sent.json. Facebook stays on Postiz, and its state is read back from Postiz before it is recorded. A state is recorded only after it was read, never assumed.
- Format change, Nov 15, 2026 (owner's decision): the 7:43 AM post on Facebook and Bluesky is the day's VIDEO (the one TikTok and YouTube get), not the masthead link post. Facebook: published as a Reel, no link in the caption, the link is the first comment (door /go/fb/?ed=N&v=reel), the caption opens with the title and "link in the comments" and asks for a follow. Bluesky: video + tappable link (door /go/bsky/?ed=N&v=video) + two hashtags. Words come from tools/nd_growth_captions.py, never from an agent. It posts the video only after data/posted-edN.json shows the 7:30 task posted (so the owner's veto window is respected); otherwise the 9:43 firing sends the old link post. Switch: "video_on_facebook_bluesky" in data/social-switch.json (missing = on). Why: Facebook shows Reels to non-followers and link posts to almost nobody; the Page had 0 followers. Judge it on Dec 14 by visits through the v=reel and v=video doors against the old link-post doors.
- Matchdays, since Nov 15, 2026 (owner's decision): the full-time card also goes on the Facebook Page (Reel, link in the first comment) and Bluesky (video + link + tags), after the one-shot has put it on TikTok and YouTube. A task at 11:37 AM, 3:37 PM and 5:37 PM ET does nothing on a day without a match; on a matchday it waits for data/posted-ft-<date>.json, then posts with the words of tools/nd_growth_captions.py --ft. Doors /go/fb/?ed=N&v=ft and /go/bsky/?ed=N&v=ft land on /subscribe/. Record: data/links/posted-ft-<date>.json. Switch: "fulltime_on_facebook_bluesky" (missing = on). First match: Atalanta, Sun Nov 22, 2026.
- Wednesdays, since Nov 15, 2026 (owner's decision after a check of which videos reach which channel): THE DEBATE short also goes on the Facebook Page (Reel, link in the first comment) and Bluesky (video + link + tags), after the debate task has put it on TikTok and YouTube. A task at 2:27 PM and 5:27 PM ET does it; words from tools/nd_growth_captions.py --debate. The Sunday long-form stays on YouTube only (owner's choice). First run Wed Nov 18.
- Video foot, since Nov 15, 2026: every frame of the daily and full-time video reads "FREE DAILY EMAIL · nerazzurridaily.com" at its foot (tools/social_motion.py FOOT). The end card and the spoken line were already there. Checked Nov 15: with those in place YouTube sent 1 visit from 227 views in the baseline week and TikTok 0, because neither has a link a viewer can tap from the video; the TikTok caption link is kept as it is, because the 7:30 task uses it to validate the post file and to never post twice.
- Bluesky hashtags, since Nov 15, 2026: every Bluesky post of ours ends with the day's tags (three when they fit), the question post included.
- Status: Bluesky and the Facebook Page (facebook.com/nerazzurridaily) running. Threads and Instagram: skipped by the owner on Nov 14, 2026 (Threads only signs in through Instagram, and the Instagram username was already taken and not publicly visible). Do not list them as a blocker. The task would still post to Threads if the channel ever appears in Postiz. TikTok Business switch (the tappable bio link): the owner chose on Nov 14, 2026 to skip it for now; the bio keeps the typed address. Do not list it as a blocker; mention it again only if TikTok door visits become the best source.

## Partnerships
- Owns: placements won per week.
- Does: Inter Clubs abroad, English-language creators, podcasts, newsletter swaps. One pitch, one follow-up.
- Status: ready. The mailbox password secret is in place and the workflow's self-test passed on Nov 14, 2026 (23:10 UTC). No blocker. Nothing has been sent yet: the first pitches are queued by the Tuesday Nov 17 run and leave at the workflow's next run after that. Route: the outreach workflow sends through the Hostinger mailbox and reads replies.
- How: write the full message list to growth/outreach/queue.enc (Fernet, key in the private Drive file nerazzurri-outreach-key.txt), each item {id, to, to_name, subject, body, kind: pitch|followup, not_before?}. The workflow enforces: two messages per address at most, follow-up 5+ days after the pitch and only without a reply, 10 a run, 20 a day, signed Support Team. Read growth/outreach/state.enc for what was sent and who replied; status.json has counts.
- Owed mentions: add {"date", "name", "url", "text"} to data/mentions.json (public). The renderer prints it in that date's edition, page and email, as "From our friends."

## Community
- Owns: replies and referral signups.
- Running since Nov 15, 2026: a task (11:23 AM and 5:23 PM ET) answers every viewer who comments under our own YouTube videos, as the channel (and, in the same run, people who wrote to us on Bluesky and visitors who commented on our Facebook Page's posts). Facts only from the edition data, with the edition's confirmed or reported label; an opinion gets an answer and a question back; the newsletter is named only when it answers what the viewer asked. At most 8 replies a run, three of ours per thread. A claimed mistake, a business or press request or a legal complaint is flagged to the owner, not answered. Record: growth/community/replies.jsonl (ids only, no text, no names). On Mondays it adds one ledger line with the week's counts.
- Since Nov 15, 2026 it also starts one conversation a day: at 12:07 PM ET a task posts the day's question (the same one the YouTube Short asks, copied word for word from data/youtube-edN.json) on our own Bluesky account and Facebook Page. Since Nov 15, 2026 the Bluesky half goes through the repo (request data/links/bsky/edN-question.json, result in data/links/bsky/sent.json), Facebook through Postiz, and each state is read back before it is recorded. Record: data/links/question-edN.json. Switch: "question_autopost" in data/social-switch.json (missing = on). The Bluesky text (question, edition link, the day's hashtags) comes from tools/nd_growth_captions.py --question since Nov 15, 2026; that tool also accepts a question followed by a short prompt ("Name one."), which the first rule would have skipped (14 of editions 40 to 75). Replies on Bluesky reach the answers task; comments on the Facebook Page are read and answered by the replies task since Nov 15, 2026 (owner signed the Page in to the Facebook connection that day): PART C of that task reads the Page's posts of the last 14 days and their comments, answers visitors under the same rules as YouTube (facts from the edition data only, three of ours a thread at most, 8 a run, flags for claimed mistakes and business requests), and may give one tappable link through the door /go/fb/?v=reply. It never comments anywhere but under our own posts. Reading was tested on Nov 15 (8 posts, one comment, ours); the first reply is the test of sending.
- Also running: the daily question comment on YouTube and the Wednesday debate (other tasks).
- Bluesky (owner's choice Nov 14, 2026: answer only people who reply to, mention or quote us): running. The workflow bluesky.yml (every three hours, and at once when the queue is committed) reads who wrote to us into the encrypted growth/community/bsky-state.enc and sends the answers the Community task queues in bsky-queue.enc. tools/nd_bsky.py refuses any reply to a post that was not addressed to us, a second answer to the same post, more than three answers to one person in a thread, a link to another site, and never likes, reposts, follows or messages. Counts only in growth/community/bsky-status.json. Replying to strangers' posts stays off: Bluesky asks automated accounts not to.
- Reader mail (since Nov 15, 2026): a task at 9:47 AM and 4:47 PM ET reads what readers wrote to the site mailbox (encrypted in growth/outreach/state.enc) and answers each person once, through the outreach workflow, kind "reader". The mail tool refuses a reader message to anyone who did not write first, to a partner address, or to a message older than 14 days. A claimed mistake, a business request or a legal complaint is flagged to the owner; an unsubscribe request is carried out in Brevo. What readers ask for, without names: growth/community/reader-notes.md.
- Later: a refer-a-friend link.
- Status: YouTube running. First run Nov 15, 2026 at 11:24 AM ET succeeded; the YouTube reads work (checked the same hour: 16 comment threads on the channel, all our own, no viewer comment has ever been posted), so there was nothing to answer and nothing was recorded. Sending a YouTube reply is still unexercised: the first viewer comment is the test. Bluesky: running since Nov 15, 2026. The app password secret is in place, the self-test passed (login and notification read) and the first real read found nobody waiting. A real send has not happened yet; the first answer is the test.

## Builder and Reviewer (the weekly build, since Nov 15, 2026)
- Own: one useful build a week, live without the owner. Queue: growth/build-queue.md, first `ready` item first.
- Builder (Fridays 3:41 PM ET): builds one item on a branch named build/..., opens a pull request, never merges. May change only tools/nd_evergreen.py and new tools/nd_growth_*.py; at most 250 lines; facts from the edition data only.
- Reviewer (Saturdays and Tuesdays 1:19 PM ET): a separate agent that did not write it. Checks the files, the size, the automatic checks, the whole diff, rebuilds the site to confirm the edition pages are byte-identical, reads the new page; then merges or rejects. Never edits code.
- Every workflow's push retry uses rebase --autostash (Nov 15, 2026), so an agent's commit landing during a build no longer stops the edition from publishing.
- A merged build goes live with the next morning's edition (the edition workflow commits any page folder listed in build/evergreen-paths.txt). Undo = revert the one commit.
- Not theirs: the edition, the email, the videos, workflows, the navigation bar, scheduled tasks, money, passwords, accounts.
- Status: running. First build Fri Nov 20, 2026 (transfer news page); first review Sat Nov 21.
