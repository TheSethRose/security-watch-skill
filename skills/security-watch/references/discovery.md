# Discovering the stack

Build the inventory from evidence, then confirm it with the user. Don't assume a cloud, a hosting panel, an OS or a language. Many people run a mix: a laptop, a few repos on a managed platform, a VPS or two, and some sites.

## 1. Gather what's already known

Check these before asking anything:

- **This conversation:** projects, servers, domains, providers and tools the user mentioned, plus anything they said about past patching.
- **Memory and instructions:** the host's memory files, global and project instruction files (`CLAUDE.md`, `AGENTS.md`), and notes the user points you to.
- **Previous state:** an existing `inventory.md` or ledger, or another tool's config the user already keeps for this.

## 2. Inspect, read-only

Only look where the user expects you to.

**Device.**
- OS and version: `sw_vers`, `/etc/os-release`, `winver` or `Get-ComputerInfo`.
- Package managers in use: Homebrew, apt/dnf, winget/Scoop/Chocolatey, Mac App Store (`mas`).
- Language runtimes and their version managers: nvm, fnm, volta, pyenv, uv, rbenv, asdf, mise.
- Docker or another container runtime.
- Browsers, and desktop apps that embed browsers (Electron apps such as chat, notes and password-manager clients).
- VPN and remote-access tools.
- AI tooling: agent CLIs, editor extensions and MCP servers. These run code with the user's permissions, so they're in scope. If there are any, set up the agent privacy check too ([agent-privacy.md](agent-privacy.md)).

**Projects.**
- Ask where their code lives, or look in the usual places (`~/code`, `~/Developer`, `~/projects`, `~/src`).
- Prefer repos with recent commits, and confirm which ones matter.
- In each project, note:
  - lockfiles: `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lock`, `uv.lock`, `poetry.lock`, `requirements*.txt`, `Gemfile.lock`, `go.sum`, `Cargo.lock`, `composer.lock`, `*.csproj`;
  - Dockerfiles and compose files, with their base images;
  - runtime pins: `.nvmrc`, `.node-version`, `.python-version`, `engines`, `.tool-versions`.

**Hosting signals.** Treat these as hints, not answers, and confirm with the user:

| Signal | Likely host |
|---|---|
| `vercel.json`, `.vercel/` | Vercel |
| `netlify.toml` | Netlify |
| `fly.toml` | Fly.io |
| `render.yaml` | Render |
| `railway.json`, `railway.toml` | Railway |
| `wrangler.toml`, `wrangler.jsonc` | Cloudflare Workers/Pages |
| `app.yaml` | Google App Engine |
| `firebase.json` | Firebase |
| `amplify.yml` | AWS Amplify |
| `Procfile` | Heroku or a Heroku-style host such as Dokku |
| `config/deploy.yml` with Kamal keys | Kamal on the user's servers |
| Kubernetes manifests, Helm charts, Terraform | ask which cluster or cloud |
| CI deploy steps in `.github/workflows/*`, `.gitlab-ci.yml` | read the deploy step: ssh, a CLI, a webhook to a panel such as Coolify, CapRover or Portainer |

**Installed and signed-in CLIs.** Each of these is a hint: `vercel`, `netlify`, `flyctl`, `railway`, `render`, `wrangler`, `heroku`, `gcloud`, `aws`, `az`, `doctl`, `coolify`, `kubectl`, `gh`, `glab`. Use only read-only listing commands. If a CLI isn't signed in, note it; don't sign in for the user.

**Servers.** `Host` entries in `~/.ssh/config` are candidates. Ask which ones are the user's servers and which are worth checking. Some may be work machines they shouldn't touch.

**Sites.** Domains often appear in configs, READMEs, `CNAME` files, `package.json` `homepage` and env examples. Confirm the list. Two read-only checks hint at the host:

- `dig +short CNAME <domain>`. Targets like `*.vercel-dns.com`, `*.netlify.app`, `*.fly.dev`, `*.onrender.com`, `*.up.railway.app`, `*.pages.dev`, `*.github.io`, `*.herokudns.com`, `*.azurewebsites.net` and `*.cloudfront.net` point to those platforms. A plain A record usually means a server they run, so ask which.
- `curl -sI https://<domain>`. Headers such as `server: Vercel` / `x-vercel-id`, `x-nf-request-id` (Netlify), `fly-request-id`, `x-render-origin-server`, `x-github-request-id` and `server: cloudflare` with `cf-ray` hint at the host. Cloudflare is often only a proxy in front of something else. `x-powered-by` and `server` can reveal framework and server versions worth matching against advisories.

## 3. Confirm in one message

Show a draft inventory grouped by area and ask the user to correct it in one reply. Don't run a long questionnaire. Ask only what you couldn't find:

- which projects and sites are in production;
- where each one is hosted;
- which servers are theirs;
- anything they already know is vulnerable, or have decided to accept;
- if they use AI agents: the personal details to watch for in agent requests, and which domains are theirs ([agent-privacy.md](agent-privacy.md)).

Their answers about known issues go straight into the ledger ([ledger.md](ledger.md)).

## 4. Write `inventory.md`

```markdown
# Inventory (updated <date>)

## Device
- macOS 27.1 (Apple silicon); Homebrew; Node 24 via fnm; Python via uv; Docker Desktop
- Apps worth tracking: Chrome, Slack, 1Password, Tailscale
- AI tools: <agent CLIs, MCP servers>

## Projects
| Project | Path | Stack | Lockfiles | Deployed to | Production |
|---|---|---|---|---|---|
| shop-web | ~/code/shop-web | Next.js 15, Node 22 | package-lock.json | Vercel | yes |
| api | ~/code/api | FastAPI, Python 3.12 | uv.lock, Dockerfile (python:3.12-slim) | Fly.io | yes |

## Hosting
- Vercel (managed runtime: patch deps and the Node version setting)
- Fly.io (Docker: we patch the base image)
- Secrets kept on each platform (names only, never values): Vercel env vars, Fly.io deploy token

## Servers
| Host | Access | OS | Runs |
|---|---|---|---|
| web-1 | ssh web-1 | Ubuntu 24.04 | Postgres 16, nginx |

## Sites
| URL | Host | Expected status |
|---|---|---|
| https://shop.example.com | Vercel | 200 |

## Credentials
<!-- Names, scopes and ages only, never values: "GitHub SSH key laptop-2025 (2025-03)", "Hetzner API token, read-write (2026-01)". -->

## Advisory sources
<!-- Pick from sources.md to match the stack above. -->

## Keywords
<!-- Product and component names to match advisories and news against: Next.js, Node.js, FastAPI, Postgres, nginx, Ubuntu, Chrome, ... -->

## Notes
<!-- How things deploy, cooldown rules, anything a later run needs to know. -->
```

Record where each fact came from when it isn't obvious ("hosting from fly.toml", "server list from user, 2026-10-22"), so a later run knows what to recheck.
