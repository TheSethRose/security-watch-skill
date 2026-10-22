# Ledger and triage

The ledger is what turns "every CVE, every day" into "what changed since we last talked", while still keeping every open, deferred and ignored finding in front of the user. Keep it accurate and the reports stay useful.

## Format

`ledger.json` in the state folder:

```json
{
  "version": 1,
  "last_run": "2026-10-22",
  "remind_after_days": 30,
  "findings": {
    "dep:shop-web:next:GHSA-f82v-jwr5-mffw": {
      "title": "Next.js middleware authorization bypass",
      "area": "dependencies",
      "where": "shop-web (package-lock.json)",
      "severity": "critical (CVSS 9.1)",
      "installed": "15.2.1",
      "fixed_in": "15.2.3",
      "status": "open",
      "first_seen": "2026-10-20",
      "last_seen": "2026-10-22",
      "last_reported": "2026-10-20",
      "note": "2026-10-20: user wants it after Friday's launch",
      "recheck": "",
      "source": "https://github.com/advisories/GHSA-f82v-jwr5-mffw"
    },
    "dep:shop-web:lodash:GHSA-xxxx-xxxx-xxxx": {
      "title": "lodash prototype pollution",
      "status": "ignored",
      "note": "2026-10-12: dev-only, only used by the test runner",
      "hidden": true,
      "hidden_on": "2026-10-19"
    }
  },
  "reviewed": {
    "https://nodejs.org/en/blog/vulnerability/october-2026-security-releases": "2026-10-22",
    "CVE-2026-12345": "2026-10-22"
  }
}
```

- `findings` holds things that need, or needed, action on the user's systems.
- `reviewed` holds every advisory, feed item or news story you looked at, whether it was relevant or not, keyed by URL or CVE. It exists so you never read the same item twice.
- When an advisory turns out to affect the user, it gets a finding as well.
- `hidden` (optional, `ignored` items only) means the user asked to stop seeing that item in reports. `hidden_on` records when.

## IDs

An ID must stay the same from run to run for the same problem. Build it as `<area>:<where>:<component>:<advisory or condition>`:

- Use the GHSA, CVE or vendor ID when there is one: `dep:shop-web:lodash:GHSA-xxxx`, `image:postgres:16-alpine:CVE-2026-1234`.
- Use a short condition name when there isn't: `server:web-1:reboot-required`, `server:web-1:apt-security:openssl`, `site:shop.example.com:tls-expiry`, `device:mac:macos-update`, `platform:render:node-runtime-eol`.
- Leave out anything that changes daily, such as candidate version numbers or dates. Otherwise the same issue looks new every time a new build appears.
- The same advisory in three projects is three IDs, but report them together as one line.

## Statuses

| Status | Meaning | Reported when |
|---|---|---|
| `open` | Needs action and has been reported. | Every run under To do. Under Action needed when it changes, or once as a reminder after `remind_after_days`. |
| `fixing` | Approved and in progress, for example "fix merged, awaiting deploy". The note says what's left. | Every run under Deferred, saying what's left, until verified. |
| `waiting` | Blocked on upstream or on a date. `recheck` says exactly what to check. | Every run under Deferred, with its recheck. Under Action needed when the trigger fires. |
| `accepted` | The user chose to live with it. Record why, plus an optional `recheck`. | Every run under Deferred, with the reason. Under Action needed when its recheck fires or it gets materially worse. |
| `ignored` | False positive or doesn't apply. Record why. | Every run under Ignored, with the reason, unless `hidden`. Hidden ones are counted, not listed. |
| `fixed` | Verified gone. Keep it for 90 days so a regression is noticed. | Once under "Fixed since last run". If it reappears, as a regression under Action needed. |

Every finding that isn't `fixed` appears in every report, in exactly one section. That way a deferred item can't be forgotten just because nothing about it changed.

## Classifying a run

Compare each result with the ledger:

- **New:** the ID isn't in the ledger, and the advisory isn't in `reviewed`. Add it as `open` with `last_reported` set to today.
- **Changed:** something known changed in a way that changes what the user should do:
  - a fix became available;
  - severity went up;
  - it was added to CISA KEV or is otherwise reported as exploited;
  - it became internet-facing;
  - it came back after being `fixed` (a regression).
  Report it and update the entry.
- **Due:** a `waiting` or `accepted` item whose recheck condition is now met: the date has passed, the upstream fix shipped, or the watched version exists. Also an `open` item last reported more than `remind_after_days` ago, which gets one reminder line. Report it and reset `last_reported`.
- **Unchanged:** everything else. Update `last_seen` and list it in its section: `open` under To do, `waiting`, `fixing` and `accepted` under Deferred, and `ignored` under Ignored (unless `hidden`). Group lines by root cause and name every component in the group.
- **Resolved:** a check that ran successfully no longer finds it. Verify it, then mark it `fixed` with the date and evidence. Never resolve an item because its check failed or was skipped.

Fill in a recheck so the next run can test it without judgment. Good: "Homebrew `node` formula ≥ 26.12.1", "after 2026-11-01", "https://github.com/owner/repo/pull/123 released". Bad: "check later".

## Recording conversation decisions

When the user says something about an issue, record it straight away with the date and their words in short:

- "That's dev-only": `ignored` or `accepted`, saying why.
- "I'll do it after launch": stays `open`, with a note, and `recheck` set to the date.
- "Fixed it": `fixing` until you verify it on the running system, then `fixed`.
- "Stop showing me that one" about an `ignored` item: set `hidden: true` and `hidden_on` to today. "Show me the hidden ones" lists them; "show that one again" removes the flag. If it is about a deferred or open item, ask whether to ignore it first, because only ignored items can be hidden.

When setting up for someone who has already been patching, add what they've told you before the first run, so the baseline doesn't re-announce things they handled.

## First run

On the first run everything is New. Don't dump hundreds of lines on the user:

1. Report the real action items: exploited, critical or internet-facing issues with a fix available.
2. List the rest under To do, grouped by root cause and naming the components, for example "shop-web: 37 dependency findings (2 critical): next, lodash 3, braces 2, …".
3. Mark everything reported or summarized as `open`, with `last_reported` set to today.
4. Offer to go through the backlog with them once, setting each item to `accepted`, `ignored`, `waiting` or a fix. From then on it shows under Deferred or Ignored instead of To do.

## Upkeep

- Drop `reviewed` entries older than the advisory lookback window plus 30 days. Feeds won't show them again.
- Drop `fixed` entries after 90 days.
- Keep `ignored` and `accepted` entries while the component is still installed.
- Write the file atomically: write to a temp file, then rename it, so an interrupted run can't corrupt it.
