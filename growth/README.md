# Growth team

Started Nov 14, 2026. The owner approved the Growth Team Plan (private doc) and all four recommendations.
This folder is the team's memory: every agent run reads it first and writes to it last.
Never write an email address, a subscriber's name or the owner's name in this folder.

## The score
Real subscribers: confirmed by double opt-in, with owner, family, test and project addresses excluded.
The Scorekeeper (the Monday numbers task) is the only source of the score. No agent reports its own results.

## Files
- targets.json: baseline and checkpoints. Re-based once, at the Dec 14 review, then held.
- briefs.md: each agent's one number, what it may do alone, current priority. Only the Growth Lead edits it.
- guardrails.md: rules no agent may break and the Lead may not relax.
- decisions.md: what the owner decided, with dates. Only the owner's own decisions go here.
- build-queue.md: what gets built next, in order. The Builder takes the first ready item; the Reviewer puts it live.
- ledger.jsonl: one JSON object per line, append only. Every run that changes something logs it BEFORE the change takes effect:
  {"date","agent","action","expected","check_by","result"} - result stays null until the Lead fills it at check_by.

## Rules the Lead applies
1. A channel or tactic with no real visits after four weeks is paused; its effort moves to what works.
2. A channel that produces subscribers gets more volume the next week.
3. An experiment with no result by its check_by date counts as a failure.
4. Two missed weekly targets in a row: the plan changes. The memo leads with the miss and the change.
5. A finding that undercuts something the owner approved goes in the memo's first line, and work on it stops until he decides.

## The signup funnel (since Nov 14, 2026, about 23:00 UTC)
One view of /subscribe/sent/ = one signup sent (the form loads it in a hidden frame; its referrer path is the page the person signed up on). One view of /subscribe/confirmed/ = one confirmation click. Drop rows with bot = 1 or a "Headless" browser.
Test rows to ignore: Nov 14, 2026, 22:53 and 22:55 UTC, referrer /match/atalanta-vs-inter-2026-11-22/ (two test signups with a stubbed form; no address reached the mailing list).

## The reader question (since Nov 15, 2026)
Each email ends with "Was today worth your 90 seconds? Yes · Not today". A tap is one view of /go/vote/ed<N>/yes/ or /go/vote/ed<N>/no/ (then the reader lands on /thanks/). The Lead reads them for the week with the same Cloudflare query as the signup funnel, with requestPath_like "/go/vote/%", drops bot and Headless rows, and reports yes and no counts and the share of delivered emails that tapped, under "What moved". Two No answers for every Yes for two weeks running is a finding for the memo's first line.

## Reader mail (since Nov 15, 2026)
Readers answer the edition and the welcome email by reply. The Community agent reads those messages (encrypted, in growth/outreach/state.enc) and answers each person once through the outreach workflow, kind "reader". What readers ask for, with no names, is kept in growth/community/reader-notes.md; the Lead names the most-asked topic in the memo.
