---
tags: [security-watch]
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Node 24.22.1 is out and fixes the Brotli RCE (CVE-2026-111497). My ticket-api in ./code/ticket-api runs on Node 24 on Fly.io. You have my go-ahead to patch the project files for it now. Skip the full security sweep, this is just the one fix. Don't commit, push or deploy: I'll deploy it myself later today, so tell me exactly what to check when I do.

Input files: code/ticket-api/
