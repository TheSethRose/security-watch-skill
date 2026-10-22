# Advisory sources

Scanners only know about packages in lockfiles and images. Advisories catch the rest: the OS, runtimes, servers, proxies, panels, desktop apps, CA incidents and supply-chain attacks. Some also give early warning before scanners update.

Contents: how to read them · general · operating systems · runtimes · frameworks · infrastructure · platforms · desktop apps · news and supply chain · generic patterns.

## How to read them

- Pick the sources that match the inventory, and record the list in `inventory.md`. Ten well-chosen sources beat fifty.
- Fetch the feed, keep only items published since the last run (or the last 3 days on a first run), and skip anything already in the ledger's `reviewed` map.
- For high-volume sources (news, mailing lists, CISA), keep only items that mention an inventory keyword. A keyword hit is a lead, not proof: "Prisma" might be Palo Alto Prisma. Open the item only when its title or summary looks relevant.
- For an item that may apply, confirm the affected and fixed versions on the vendor's page, then compare them with what's installed.
- Add every item you considered to `reviewed`, including the irrelevant ones, so it's never read twice.

Feeds are RSS, Atom or RDF. Parse the date from `pubDate`, `published`/`updated` or `dc:date`.

## General

| Source | URL | Notes |
|---|---|---|
| CISA Known Exploited Vulnerabilities | https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json | JSON. Filter by `dateAdded`. Treat any match with the stack as urgent. |
| CISA advisories | https://www.cisa.gov/cybersecurity-advisories/all.xml | Mostly ICS; keyword-filter it. |
| oss-security mailing list | https://seclists.org/rss/oss-sec.rss | Early disclosure for open source; keyword-filter it. |

## Operating systems

| Source | URL | Notes |
|---|---|---|
| Apple security releases | https://support.apple.com/en-us/100100 | HTML table (name, date); no feed. |
| Ubuntu security notices | https://ubuntu.com/security/notices/rss.xml | Filter by release (e.g. `24.04`, `noble`). |
| Debian security advisories | https://www.debian.org/security/dsa | RDF feed. |
| Microsoft security update guide | https://api.msrc.microsoft.com/update-guide/rss | Large; keyword-filter it. |

## Runtimes and languages

| Source | URL |
|---|---|
| Node.js security releases | https://nodejs.org/en/feed/vulnerability.xml |
| Bun releases | https://github.com/oven-sh/bun/releases.atom |
| Deno releases | https://github.com/denoland/deno/releases.atom |
| Python (filter "security") | https://pythoninsider.blogspot.com/feeds/posts/default |
| Go blog (security releases are announced there) | https://go.dev/blog/feed.atom |
| PHP releases | https://www.php.net/releases/feed.php |
| Ruby news | https://www.ruby-lang.org/en/feeds/news.rss |

## Frameworks

Dependency scanning already covers library advisories for packages in lockfiles. Add a framework's advisories here only for early warning, or when it isn't in a lockfile. For any GitHub repo: `gh api "/repos/<owner>/<repo>/security-advisories?state=published&sort=published&direction=desc&per_page=20"`, or unauthenticated `https://api.github.com/repos/<owner>/<repo>/security-advisories`.

Repos that publish advisories this way include:
- JavaScript: `vercel/next.js`, `vitejs/vite`, `remix-run/react-router`, `sveltejs/kit`, `nuxt/nuxt`, `honojs/hono`, `expressjs/express`, `fastify/fastify`, `better-auth/better-auth`;
- other languages: `rails/rails`, `laravel/framework`.

Django and WordPress post on their own sites:

| Source | URL |
|---|---|
| Django (filter "security") | https://www.djangoproject.com/rss/weblog/ |
| WordPress security | https://wordpress.org/news/category/security/feed/ |

## Infrastructure

| Source | URL |
|---|---|
| Docker Engine (Moby) advisories | `gh:moby/moby` (pattern above) |
| containerd, runc advisories | `gh:containerd/containerd`, `gh:opencontainers/runc` |
| Kubernetes official CVE feed | https://kubernetes.io/docs/reference/issues-security/official-cve-feed/feed.xml |
| Traefik advisories | `gh:traefik/traefik` |
| Caddy advisories | `gh:caddyserver/caddy` |
| nginx news (security releases) | https://nginx.org/index.rss |
| PostgreSQL news (filter titles: "Released", "security") | https://www.postgresql.org/news.rss |
| Redis advisories | `gh:redis/redis` |

## Platforms and panels

| Source | URL |
|---|---|
| Coolify releases / advisories | https://github.com/coollabsio/coolify/releases.atom, `gh:coollabsio/coolify` |
| Vercel changelog (large) | https://vercel.com/changelog/rss.xml |
| Cloudflare blog | https://blog.cloudflare.com/rss/ |
| Supabase blog | https://supabase.com/rss.xml |
| GitLab security releases | https://about.gitlab.com/security-releases.xml |
| GitHub security blog | https://github.blog/category/security/feed/ |

For other panels and self-hosted apps, use the GitHub patterns below on their repo.

## Desktop and network apps

| Source | URL |
|---|---|
| Chrome (titles "Stable Channel Update for Desktop") | https://chromereleases.googleblog.com/feeds/posts/default |
| Electron advisories (affects chat, notes, password-manager clients) | `gh:electron/electron` |
| Tailscale security bulletins | https://tailscale.com/security-bulletins/index.xml |

## News and supply chain

Keyword-filter all of these. They're how compromised packages, CA incidents and broad campaigns usually surface first.

| Source | URL |
|---|---|
| BleepingComputer | https://www.bleepingcomputer.com/feed/ |
| The Hacker News | https://feeds.feedburner.com/TheHackersNews |
| Socket (npm/PyPI malware) | https://socket.dev/api/blog/feed.atom |
| StepSecurity (CI/GitHub Actions) | https://www.stepsecurity.io/blog/rss.xml |
| Aikido | https://www.aikido.dev/blog/rss.xml |

When a supply-chain story names compromised versions, search every lockfile and the device's global tool installs for them, for example `npm ls -g`, `pip list`, `uv tool list` and `pipx list`. The answer is usually "not affected", and saying so with evidence is useful.

## Generic patterns

- Releases for any GitHub repo: `https://github.com/<owner>/<repo>/releases.atom`.
- GitHub global advisory database: `gh api "/advisories?ecosystem=npm&affects=<package>"`.
- OSV for one package version: `curl -s https://api.osv.dev/v1/query -d '{"package":{"name":"<name>","ecosystem":"npm"},"version":"<version>"}'`.
- NVD for one CVE: `https://nvd.nist.gov/vuln/detail/<CVE-ID>`.
