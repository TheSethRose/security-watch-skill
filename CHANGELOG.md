# Changelog

The skill's version is `metadata.version` in `skills/security-watch/SKILL.md`. The skill reads this file to tell you what changed when an update is available.

## 1.10.0 (2026-11-07)

- Every run now checks your AI agents' settings files for saved secrets. Some agents save an approved command word for word, so a password you typed can end up in a file such as `.claude/settings.local.json`. A new script finds these, including ones already deleted but still in git history. It shows only the file, the kind of secret and a count, never the value.
- Committed secrets are treated as exposed, so the next step is to rotate them. Ones that never left your machine rank lower.

## 1.9.0 (2026-10-30)

- Every run now checks pwn.watch, a live incident tracker, for software you run. Patch incidents are compared with your installed versions, supply-chain incidents are checked against your lockfiles, and breaches are flagged only for services you use.
- Incidents that change after the last run (a fix ships, more versions are affected) are re-read, so updates aren't missed.

## 1.8.0 (2026-10-25)

- Known-compromised package versions are kept in a `known-bad.md` file in your state folder, each with its evidence. Every run checks your lockfiles and global installs against it first, offline. The skill adds entries from supply-chain stories it reads.
- Reports now say what the skill could not see ("Could not see: X. Would need: Y."), and a clean result is worded as "nothing known found", not "safe".
- Before a fix is marked `fixed`, the skill searches everything you run for the same vulnerable version or setting, and records the search so the next run can repeat it.
- Each dependency finding records whether the vulnerable code is reachable. A finding the skill can't confirm stays in To do. It is never ignored on a guess.
- Secrets: the skill reads a token's role and expiry offline when it can, never sends a secret anywhere without your approval, and ranks live secrets higher. Placeholder and test values are labelled and ranked lower, not dropped.
- Optional read-only lockfile checks: unexpected registry hosts, missing or weak integrity hashes, git and tarball dependencies, install scripts, and versions newer than your release-age cooldown.
- When there are signs of compromise, the report adds a short "was it exploited?" triage: scope and time window, log integrity, ongoing or finished, and whether a probe was really a breach.
- New self-test for the agent privacy script, and a new eval case for unconfirmed reachability.

## 1.7.2 (2026-10-24)

- Desktop app versions are read from the app's metadata (`Info.plist` on macOS), never by running the app. Running a desktop app with `--version` starts it, and could crash it with an error dialog.

## 1.7.1 (2026-10-24)

- Shorter skill description, so the skill costs less context in every conversation. It now also triggers when you ask for help with a single security fix, so the fixing rules apply then too.

## 1.7.0 (2026-10-24)

- Optional threat notes for each project in the inventory: where untrusted input enters, what matters most, what is out of scope, and how you rate severity. Setup drafts them from `SECURITY.md`, threat models and READMEs.
- Triage applies them: out-of-scope findings are listed as ignored with the reason, and your severity rating is shown next to the advisory's and sets the order of Action needed.

## 1.6.2 (2026-10-23)

- Secrets and credentials checks no longer assume particular tools: they use whatever CLI, API or settings page the user has, and say which.
- More places to check for hidden access: SSH login keys on every machine, macOS profiles, Linux shell startup files and the Windows Startup folder. Startup entries are saved as a baseline, so later runs show only what's new.
- Container checks catch secret files copied into images.
- A secret someone else is using gets revoked first. A compromised machine still gets a full report, with nothing fixed until it's clean.

## 1.6.1 (2026-10-23)

- New secrets and credentials checks: secrets in code, history and container images (names and locations only), and an inventory of keys and tokens with their age.
- Device checks list what starts on its own, and check global packages against indicators from malicious-package advisories.
- Fixing rules: rotate secrets in a safe order, clean a compromised machine before rotating, and confirm a new tool's source before installing it.

## 1.6.0 (2026-10-23)

- New server exposure checks: what listens, what the provider firewall allows, what public scanners see, whether sites behind a CDN can be reached straight at the origin, and whether hostnames bypass the CDN.
- Recommendations to close each gap, smallest first: web ports only from the CDN, SSH and admin ports only over a private network, no public database ports, and optionally an outbound tunnel.

## 1.5.0 (2026-10-23)

- Device checks look past the system copy: tools that bundle their own runtime or library, and long-running processes that still have the old one loaded after an upgrade.
- When an advisory publishes a test endpoint, each affected client is tested against it, because clients keep separate trust stores and libraries.
- Reachability uses what's listening on all interfaces, and, for client-side bugs, what fetches untrusted content.
- A breach at a platform where you keep secrets is a finding. The fix is rotating those secrets.
- Mitigations that an OS or package update can undo get rechecked after each update.
- Fixing rules: back up and note the undo before a config change, say what a service does before restarting it, never pipe a remote script into a shell, ask before every `sudo`, and hand dialogs and passwords to you. Reports keep out process arguments, environment variables and file contents, and say what a check couldn't see.

## 1.4.0 (2026-10-23)

- New agent privacy check, for anyone who uses AI agents. `scripts/agent_privacy.py scan` reads Claude Code and Codex transcripts for requests that sent your email, name, phone or address to a site that isn't yours: in a header such as the User-Agent, in the URL, in a body or in a search query. You give it the details to look for. They're kept in `privacy.json` in the state folder, readable only by you.
- The same script works as a Claude Code `PreToolUse` hook. It asks you before a request sends those details to a site outside your own domains, and lets everything else through. Set `"mode": "deny"` to block those requests instead. The skill walks you through what leaked, an instruction for your agents, installing and testing the hook, and closing the findings.

## 1.3.0 (2026-10-22)

- Fixes cover every place a runtime version is set: Dockerfile stages, version files, `packageManager` and CI setup steps. A floating CI version gets `check-latest: true` or a pinned patch.
- How an image is pinned decides the fix: an exact tag moves to the fixed tag, a digest pin gets the new digest, and a floating tag gets a fresh rebuild.
- Container fixes are tested in the built image: confirm the version inside it, start it, and check a health route.
- Before a deploy, the skill notes what to roll back to.
- A mitigation is recorded on a `waiting` item and never counts as a fix.

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
