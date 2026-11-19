# Search: weekly review

Written by the Search agent on Thursdays from Google Search Console (web search, data state "all"). Rewritten every week; the last four weeks' summary lines are kept at the bottom.

## Week of Nov 12 to 18, 2026 (review of Nov 19)

**This week in one line:** 1 click and 95 impressions at average position 9.3, against 1 click and 132 impressions at 10.4 the week before (Nov 5 to 11): clicks flat, impressions down 37 (28%).

Read it with two cautions. Google still marks Nov 18 as incomplete. And the whole fall is the home page on the single word "nerazzurri" (106 impressions to 45); the pages built for search went the other way, from 3 impressions to 39.

The one click was the first search click on a page built for search: /injuries/, on the query "dimarco injury update", where the page stood at position 1.5.

## By page group

| Page group | Clicks | Impressions | Avg position | Week before (clicks / impressions / position) |
|---|---|---|---|---|
| Home | 0 | 45 | 10.7 | 0 / 106 / 9.6 |
| Editions (/p/) | 0 | 11 | 11.5 | 0 / 22 / 15.5 |
| /fixtures/ | 0 | 0 | none | 0 / 3 / 4.3 |
| /results/ | 0 | 1 | 1.0 | 0 / 0 / none |
| /injuries/ | 1 | 36 | 7.1 | 0 / 0 / none |
| US TV guide | 0 | 2 | 7.0 | 0 / 0 / none |
| /match/ pages | 0 | 0 | none | 0 / 0 / none |
| Other (an old /t/edition address) | 0 | 0 | none | 1 / 1 / 1.0 |
| **All** | **1** | **95** | **9.3** | **1 / 132 / 10.4** |

- /injuries/ was shown 36 times in its first week in Google and is already the second most shown page of the site, ahead of every edition.
- /fixtures/ had 17 impressions at position 5.9 over the last 28 days but none this week. Google last fetched it on Nov 11, before the match pages existed.
- No /match/ page has been shown for any search yet (28 days, zero rows). The one match search we appeared for, "inter milan vs genoa" (position 7), showed /injuries/, not the Genoa page.

## Index status (inspected Nov 19)

| Page | Status | Last fetched by Google |
|---|---|---|
| /match/atalanta-vs-inter-2026-11-22/ | Discovered, currently not indexed | never |
| /match/inter-vs-vfb-stuttgart-2026-11-25/ | Discovered, currently not indexed | never |
| /match/inter-vs-genoa-2026-11-28/ | Indexed | Nov 17 |
| /fixtures/ | Indexed | Nov 11 |
| /results/ | Indexed | Nov 16 |
| /injuries/ | Indexed | Nov 16 |
| /how-to-watch-inter-milan-in-the-usa/ | Indexed | Nov 16 |

5 of 7 indexed. No page is "unknown to Google", so the sitemap was not resubmitted: Google has both missing match pages from the sitemap and has not fetched them yet. The Atalanta match is in three days and its page will probably not be in Google in time.

Two things seen while inspecting:
- Match pages are linked from only two pages, /fixtures/ and the US TV guide. The home page, /results/, /injuries/ and the editions carry no link to any match page. Google's record for the Atalanta page shows no page linking to it; the Stuttgart and Genoa pages show the US TV guide only.
- Google reads the match page's event markup as valid (Genoa page: Events, pass), with warnings for optional fields only (image, end date, performer, organizer, offers).

## Queries close to page one (last 28 days, average position 5 to 20)

Injury searches, all landing on /injuries/:

| Query | Impressions | Position |
|---|---|---|
| inter milan injury update | 5 | 6.8 |
| inter milan injury list | 2 | 6.5 |
| inter milan injuries | 2 | 8.0 |
| inter milan injury news | 2 | 15.5 |
| inter injury players | 1 | 9.0 |
| inter milan injured players | 1 | 10.0 |

Already above position 5 on the same page: "dimarco injury update" (2 impressions, 1.5, 1 click) and "inter milan injury list and return date" (1 impression, 1.0).

What would move them: these searches ask who is out and until when, by player. The page answers with a log by date, so the searcher has to read 32 items to find one player. A list by player at the top is the answer the query asks for (see the proposal).

The club's nickname, all landing on the home page:

| Query | Impressions | Position |
|---|---|---|
| nerazzurri | 194 | 10.8 |
| nerazurri, nerazzuri and six other spellings | 35 | 7 to 10.6 |
| inter daily | 3 | 7.7 |
| inter milan nerazzurri | 1 | 10.0 |
| inter milan blog | 1 | 6.0 |

What would move them: very little, and it would not be worth much. 229 impressions on the nickname in 28 days brought no click; a person typing the one word wants the club, not a newsletter. This is the site's largest impression count and its weakest. Do not build for it.

Others between 5 and 20: "inter milan vs genoa" (1, position 7, shown /injuries/; the Genoa match page was indexed on Nov 17 and should take this over), one player-name search and one fans-in-Rotterdam search landing on editions (1 impression each).

Queries no page of ours is built for: "inter milan news" (2 impressions, position 42), "inter fc news" (46), "inter 1908 fc news" (85), "derby inter milan" (32). All far from page one, all on words every large outlet competes for. No transfer search appears in the 28 days.

## Proposal: a "who is out" list by player at the top of /injuries/

One change to one page: above the dated log, a section with one entry per player who has an injury item in the last 30 days of editions. Each entry gives the player's name, the newest item about him (its headline, its CONFIRMED or REPORTED label, its source line and date) and, under it, his earlier items by date with links to their editions. Each entry gets its own anchor (/injuries/#dimarco). The page title and first line change to say what the searches say: injury list and updates, by player.

Queries that justify it: the eight injury searches above (16 impressions, positions 1 to 15.5, the week's only click), on a page that reached 36 impressions at position 7.1 in its first week. Two of them name what the page lacks: a player ("dimarco injury update") and a list with return dates ("inter milan injury list and return date").

Built from: the same injury items the page already selects from data/edition-*.json (headline, first paragraph, source line, label, edition number, date). The player is taken from the headline of each item; a name counts when it appears in the headlines of two or more injury items, and words that are an outlet (from the source lines) or an opponent (from the fixture rows) are left out. A return date is printed only where an item's own text gives one, in the item's words. Nothing is written by hand and no squad list is needed.

Why it is not a thin page: it adds no new address. It makes one existing page answer a second kind of question, with the same items grouped another way.

Risk for the Builder to settle: taking names from headlines by rule can miss a player or pick a wrong word. If the rule cannot be made reliable in testing, the entry falls back to the dated log as it is today.

Not proposed, noted for the Lead: a row of links to the next three match pages on the home page and on /results/ and /injuries/ would give Google a path to each match page before its match. It touches shared page parts, so it is the Lead's call whether it is a Builder item.

## Summary lines (last four weeks)

- Nov 12 to 18, 2026: 1 click, 95 impressions, position 9.3 (week before: 1 / 132 / 10.4). /injuries/ 1 click, 36 impressions at 7.1 in its first week. 5 of 7 inspected pages indexed. Proposal: who-is-out list by player on /injuries/.
