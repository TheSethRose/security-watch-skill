---
type: llm
focus: outcome
weight: 1
---

The setup-node step in code/ticket-api/.github/workflows/ci.yml either pins node-version to 24.22.1 or keeps 24 and adds check-latest: true, so CI cannot run a cached older Node 24.
