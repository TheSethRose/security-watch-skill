# Changelog

The skill's version is `metadata.version` in `skills/security-watch/SKILL.md`. The skill reads this file to tell you what changed when an update is available.

## 1.2.1 (2026-10-22)

- Reports use the date and time read from the clock, never "tonight" or "this morning". A second run on the same day saves `YYYY-MM-DD-HHMM.md` instead of overwriting the day's report.

## 1.2.0 (2026-10-22)

- Every report lists every finding that still affects you, not only what's new. New, changed and due items stay under Action needed, which is still the only section that notifies you.
- New **Deferred** section: waiting, in-progress and accepted items, each with what it's waiting on (a date, an upstream fix, a deploy or your reason).
- New **Ignored** section: ignored items with their reason. Say "stop showing that one" and it's hidden from then on (`hidden` in the ledger), but still counted in the report.
- Grouped lines name every affected component.
- The skill checks for updates when it runs. In a conversation it asks whether to update first and does it for you on yes. Scheduled runs only mention it in the report.

## 1.1.0 (2026-10-22)

- Open items are listed under **To do** in every report until they are fixed, accepted or ignored, so a quiet run no longer reads as all clear.

## 1.0.0 (2026-10-22)

- First release: stack discovery, checks, advisory sources, findings ledger, report and fixing rules.
