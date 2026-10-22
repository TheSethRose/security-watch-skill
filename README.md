# Security Watch

An agent skill that finds what **you** need to patch across your devices, code, servers, hosting and websites, then works with you to fix it.

It isn't a scanner. It teaches your agent how to:

- **Learn your actual stack.** It works from your conversations, memory files, project files and a few questions. It doesn't assume Vercel, Coolify, AWS or anything else.
- **Find what's patchable** with the tools you already have: OS updates, dependency audits, image scans, SSH checks on your servers, platform settings and site TLS. It also reads advisory feeds that match what you run.
- **Remember what you've already discussed.** A local ledger records every finding and decision ("dev-only, ignore", "waiting on upstream", "fixed, awaiting deploy"). Each run flags what's new or changed under Action needed: a fix became available, severity went up, it's now exploited, or a recheck date arrived. It still lists everything else that affects you, so nothing gets forgotten: open items under To do, items waiting on a date, a fix or your reason under Deferred, and ignored items with their reason. Ask it to stop showing an ignored item and it's hidden from then on, but still counted.
- **Fix things with you.** The smallest safe change, done only with your approval and following your repo's rules, then verified on the running system rather than just in the repo.

## Quick start

Paste this into your agent:

```text
Read https://github.com/TheSethRose/security-watch-skill and help me set up a recurring security watch: install the skill, learn what I run from our chats, my memory files and my projects, ask me only what you can't find, then schedule a read-only daily check that notifies me when something new needs patching and lists everything still open, deferred or ignored.
```

## Install

With the [skills CLI](https://skills.sh):

```bash
npx skills add TheSethRose/security-watch-skill
```

This works with Claude Code, Codex, Cursor, OpenCode and any agent that reads `SKILL.md` skills. Add `-g` to install it globally.

## Use

Ask your agent things like:

- "What do I need to patch?"
- "Set up a daily security check for my projects and servers."
- "Does this new Node.js advisory affect me?"
- "Go through my security backlog with me."

On first use it builds `~/.security-watch/inventory.md` with you. It also creates `ledger.json` and a `reports/` folder. Nothing leaves your machine except read-only lookups to advisory sources.

### Tools it can use

None are required. The agent uses what's installed and says what it skipped.

| Area | Tools |
|---|---|
| Dependencies | [`osv-scanner`](https://github.com/google/osv-scanner), or ecosystem audits such as `npm audit`, `pip-audit`, `cargo audit` and `govulncheck` |
| Images | `trivy`, `grype` or `docker scout` |
| Servers and sites | `ssh`, `curl`, `openssl` and `dig` |
| Hosting | your platform's CLI, if you're signed in |

## Recurring runs

Ask your agent to schedule it, using your host's scheduled tasks, cron or launchd. Scheduled runs are read-only and notify you only when something needs action. Fixing happens when you're in the conversation.

## Updates

Each time the skill runs, it checks this repository for a newer version. In a conversation, it tells you what changed and asks whether to update before running. Say yes and it updates itself, then runs the new version. Scheduled runs only mention the update at the top of the report. Your inventory, ledger and reports are never touched by an update.

To update by hand: `npx skills update security-watch`, or `git pull` in your clone. See [CHANGELOG.md](CHANGELOG.md) for what changed.

## What it won't do

- Change anything without your approval.
- Sign in on your behalf.
- Store secrets.
- Scan systems you don't own.

## Layout

```text
skills/security-watch/
├── SKILL.md                 workflow, report format, fixing rules
├── references/
│   ├── discovery.md         learning the stack, inventory template
│   ├── checks.md            how to find patchable things, per area
│   ├── sources.md           advisory feeds and lookup APIs
│   ├── ledger.md            findings ledger and triage rules
│   └── updates.md           checking for and installing skill updates
└── evals/                   test cases (claude plugin eval)
```

## License

[MIT](LICENSE)
