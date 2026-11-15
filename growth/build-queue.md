# Build queue

The Builder (Fridays) takes the FIRST item whose status is `ready`, builds it on a branch and opens a pull request. The Reviewer (Saturdays and Tuesdays), a separate agent that did not write it, checks it and either merges it or rejects it. A merged build goes live with the next morning's edition. One build a week, one at a time.

Statuses: `ready` | `in review (PR #n)` | `merged <date>` | `live <date>` | `rejected: <why>` | `waiting on owner` | `needs a chat session`

An item is the Builder's only if it is ONE change, buildable from the edition data alone (data/edition-*.json, data/season-2026-27.json), and fits inside tools/nd_evergreen.py plus new tools/nd_growth_*.py files. Anything that touches the edition, the email, the videos, a workflow, the navigation bar or a scheduled task is `needs a chat session`. Anything involving money, a password, a new account or a change to something the owner approved is `waiting on owner`.

Order is priority. Only a chat session with the owner reorders or adds items by hand; the Builder may append the Search review's weekly proposal at the end.

## Items

1. `live 2026-11-15` — Reader question: a one-tap "Was today worth your 90 seconds? Yes / Not today" line in each email, with a vote door (/go/vote/) and a thanks page. Built and merged in a chat session with the owner.
2. `ready` — Transfer news page at /inter-milan-transfer-news/: the REPORTED items of the last 21 days that are about transfers or contracts (signing, renewal, fee, loan, clause, bid, offer, agent), newest first, each with the outlet and date exactly as the edition printed them and a link to its edition, under a line that says these are press reports, not confirmed. Plus the CONFIRMED transfer or contract items of the same window in their own section above. Why: "Inter Milan transfer news" is the most searched English query about the club and no page of ours answers it.
3. `ready` — Competition pages at /inter-milan-champions-league/ and /inter-milan-coppa-italia/: this season's results and remaining fixtures in that competition (kickoff in Eastern time first, US TV), each row linking to its match page. One build, two pages, same renderer.
4. `ready` — Match pages: add a "Last five" form line and the previous meeting this season, from the results log, where the data has them.
5. `needs a chat session` — Let the morning edition read growth/community/reader-notes.md, so what readers ask for shapes what is chased next (touches the 5:30 task prompt).
