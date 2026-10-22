# Security Watch

An agent skill that finds what **you** need to patch across your devices, code, servers, hosting and websites, then works with you to fix it.

It isn't a scanner. It teaches your agent how to:

- **Learn your actual stack.** It works from your conversations, memory files, project files and a few questions. It doesn't assume Vercel, Coolify, AWS or anything else.
- **Find what's patchable** with the tools you already have: OS updates, dependency audits, image scans, SSH checks on your servers, platform settings and site TLS. It also reads advisory feeds that match what you run.
- **Remember what you've already discussed.** A local ledger records every finding and decision ("dev-only, ignore", "waiting on upstream", "fixed, awaiting deploy"). Later runs report only what's new or has changed: a fix became available, severity went up, it's now exploited, or a recheck date arrived. Everything else is a count.
- **Fix things with you.** The smallest safe change, done only with your approval and following your repo's rules, then verified on the running system rather than just in the repo.

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
│   └── ledger.md            findings ledger and triage rules
└── evals/                   test cases (claude plugin eval)
```

## License

[MIT](LICENSE)
