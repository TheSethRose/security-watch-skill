# AGENTS.md

## Project overview

- An agent skill, not an app. Everything that ships lives in `skills/security-watch/`: `SKILL.md` (workflow), `references/` (loaded on demand), `scripts/agent_privacy.py` (Python stdlib only) and `evals/`.
- Users install it with `npx skills add` or a git clone. Every commit to `main` under `skills/` reaches them.

## Releases

Every change to `skills/security-watch/` is a release, in the same commit:

1. Bump `metadata.version` in `skills/security-watch/SKILL.md` (semver: patch for fixes and wording, minor for new checks or behavior).
2. Add a dated entry at the top of `CHANGELOG.md`, written for users: what changed for them, not how.
3. Put the version at the end of the commit subject, e.g. `fix: shorter skill description (1.7.1)`.

The skill checks for its own updates (`references/updates.md`). Git installs see any new commit as an update and show its changelog entry. Other installs compare `metadata.version`, so an unversioned change never reaches them.

Changes outside `skills/` (README, AGENTS.md, LICENSE) need no version bump.

## Validation

- Evals: `claude plugin eval skills/security-watch`. Cases are `evals/<case>/case.yaml` or `prompt.md` with `graders/*.md`, and an optional `place-files.sh` scaffold. Results land in `evals/results/`, which is gitignored.
- Add or update an eval case when changing behavior that a case covers.
- Script: `python3 skills/security-watch/scripts/agent_privacy.py --help`. Keep it stdlib-only.

## Writing style

- Short, plain sentences. Second person to the agent in `SKILL.md` and `references/`; to the user in README and CHANGELOG.
- Tool-agnostic: name a tool as an example ("such as `gitleaks`") with a fallback, never as a requirement.
- No product, vendor or app names in rules unless the rule is about that product.
- Every command in the skill must be read-only unless it's in the fixing rules. GUI apps: read versions from metadata, never run the binary.

## Safety and data

- No real personal details, hostnames, IPs, tokens or customer data in evals, examples or fixtures. Use made-up values.
- The skill must never tell agents to store secrets in the state folder, print secret values, or change anything without the user's approval. Keep those rules intact when editing.
