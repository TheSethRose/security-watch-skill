# Finding things to patch

Run the checks that match the inventory, and skip areas the user doesn't have. Every command here is read-only, apart from refreshing package metadata. When a tool isn't installed, use the fallback or note the gap under "Checked". Don't install tools without asking.

Contents: device · dependencies · containers · servers · hosting platforms · sites · AI agents · deployed vs fixed.

## Device

**macOS**
- OS updates: `softwareupdate --list` (can take a minute).
- Homebrew: `brew update` (metadata only), then `brew outdated`. Treat outdated formulae as context, not findings. Only the ones named in an advisory matter.
- Mac App Store: `mas outdated`, if `mas` is installed.

**Linux**
- Debian/Ubuntu:
  - security updates: `apt list --upgradable 2>/dev/null | grep -- -security`;
  - reboot needed: `[ -f /var/run/reboot-required ] && cat /var/run/reboot-required.pkgs`;
  - services to restart: `needrestart -r l`.
- Fedora/RHEL: `dnf updateinfo list --security` and `dnf needs-restarting -r`.

**Windows**
- Apps: `winget upgrade`.
- Windows Update: Settings, or `Get-WindowsUpdate` if the PSWindowsUpdate module is installed.
- Last patches installed: `Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 5`.

**Runtimes and apps**
- Compare installed versions with the latest security release of the branch the user is on: `node -v`, `python3 -V`, `bun -v`, `deno -V`, `go version`, `docker version`.
- Version managers can leave several runtimes installed. The default, and whatever the projects pin, are what matter.
- A project usually sets its runtime version in several places: the base image in every Dockerfile stage, version files (`.nvmrc`, `.node-version`, `.tool-versions`, `.python-version`, `.bun-version`), `packageManager`, and CI setup steps (`actions/setup-node`, `actions/setup-python`, `oven-sh/setup-bun`). Check them all, and fix them together. Fields like `engines.node` don't install anything, so leave them unless they would exclude the fixed version. A CI step with a floating version (`node-version: 24`) can run the runner's cached, older release: pin the patch or set `check-latest: true`.
- Browsers and Electron apps mostly update themselves. Check the version only when an advisory names the app.

**Bundled copies**
- Many tools ship their own copy of a runtime or library, so upgrading the system copy doesn't fix them. Examples: single-file binaries built with Bun, Deno or Node, Electron apps, statically linked Go and Rust binaries, and apps with a vendored Python or CA list. Only the tool's own release can fix those copies.
- When an advisory names a library or runtime, ask which installed tools embed it, and check each one:
  - the vendor's release notes;
  - `--version` output that names the embedded runtime;
  - `strings <binary> | grep` for its version string.
- A marker string that appears only in fixed builds is a clue, not proof. If it says unpatched, believe it. If it says patched, still confirm the version.

**Old code still loaded**
- After a shared library or runtime is upgraded, long-running processes keep the old copy in memory until they restart: services, bots, agent gateways, dev servers and terminal multiplexers. Find them with `lsof -nP | grep <library>`, or compare process start times (`ps -o lstart= -p <pid>`) with the upgrade time.
- Without sudo, `lsof` and `ps` show only the user's own processes. Say what you couldn't see under Checked.

**Test behavior when you can**
- Some advisories or incident pages publish a test endpoint, such as a site served with a revoked or compromised certificate chain. Run each affected client against it:
  - the system `curl` and HTTP stack;
  - every Python, pip and uv that installs packages;
  - Node;
  - the browsers.
- Clients keep separate trust stores and libraries, so one result doesn't cover the others. Read the advisory for what each outcome means: usually an error means safe and a success means affected. A timeout is unknown, so report it as unknown.

**Reachability**
- `lsof -nP -iTCP -sTCP:LISTEN` (macOS) or `ss -ltnp` (Linux) shows what listens on every interface (`*`, `0.0.0.0`, `[::]`) rather than only on localhost. That decides whether a bug in a service or dev server can be reached from the network.
- For client-side bugs (decoders, parsers, TLS), the exposure comes from what fetches untrusted content: browsers, agents, bots and link previewers. Tools that talk only to the user's own hosts matter less.

## Dependencies

- **First choice, `osv-scanner`.** It covers most ecosystems and lockfiles in one pass: `osv-scanner scan source -r <project> --format json`. In the JSON, `groups[].max_severity` is the CVSS score, and `affected[].ranges[].events[].fixed` gives the fixed versions.
- **Ecosystem-native fallbacks:**

  | Ecosystem | Command |
  |---|---|
  | npm | `npm audit --json` |
  | pnpm | `pnpm audit --json` |
  | Yarn (Berry) | `yarn npm audit --json` |
  | Bun | `bun audit` |
  | Python | `pip-audit` (`uvx pip-audit -r requirements.txt`) |
  | Rust | `cargo audit` |
  | Go | `govulncheck ./...` |
  | Ruby | `bundle audit` |
  | PHP | `composer audit` |
  | .NET | `dotnet list package --vulnerable` |

- **GitHub Dependabot,** if it's enabled: `gh api "repos/<owner>/<repo>/dependabot/alerts?state=open"`.

Focus by default on high and critical findings (CVSS 7+), plus anything exploited, in packages that ship to production. Note dev-only and build-only packages separately and at lower priority, but don't drop them silently.

A bundler that pins a vulnerable transitive dependency often needs an override or resolution entry rather than a direct upgrade. Check whether every dependent accepts the fixed version before suggesting one.

## Containers

- Scan the base images and app images: `trivy image --scanners vuln --severity CRITICAL,HIGH --ignore-unfixed <image>`, or `grype <image>`, or `docker scout cves <image>`.
- Check whether a newer tag of the same line exists. Many image CVEs are fixed simply by rebuilding on a fresh base.
- How the image is pinned decides the fix. An exact tag moves to the fixed tag, keeping its variant (`-slim`, `-alpine`). A digest pin needs the new digest. A floating tag (`node:24`, `latest`) needs only a rebuild with `--pull --no-cache` and a redeploy.
- CVEs that are still in the latest upstream image aren't the user's to fix. Record them as `waiting` on a newer image.
- On servers, list what's actually running: `docker ps --format '{{.Image}} {{.Status}}'`. A rebuilt image doesn't help until the container is recreated.

## Servers (SSH)

Run the Linux device checks over SSH in batch mode, so a login prompt fails instead of hanging: `ssh -o BatchMode=yes -o ConnectTimeout=10 <host> '<command>'`. If SSH asks for an interactive or browser login, report it rather than following it.

Also note:
- the kernel version against the newest installed one: a reboot is pending if they differ;
- the Docker engine version;
- versions of the database and proxy the server runs (`postgres --version`, `nginx -v`, `caddy version`, `traefik version`), to match against advisories.

## Hosting platforms

What the user has to patch depends on who runs what.

- **Managed platforms** (Vercel, Netlify, Cloudflare, Render, Railway, Heroku, App Engine, Amplify, Firebase). The platform patches the OS. The user owns:
  - the app's dependencies;
  - the runtime version setting: a Node or Python version that is end-of-life or behind on security releases;
  - for Docker-based deploys (Fly.io, Render, Railway with a Dockerfile), the base image.

  Check the platform's own security advisories and changelog. The CLIs can list projects and deployments read-only.
- **Self-hosted panels and servers** (Coolify, Dokku, CapRover, Portainer, Kamal, Docker Compose on a VPS, Kubernetes). The user owns everything:
  - host OS and kernel;
  - Docker engine;
  - the panel's version against its releases and advisories;
  - the reverse proxy (Traefik, Caddy, nginx);
  - databases and images.

  Use the panel's read-only API or CLI to list apps and their health, with whatever saved authentication the user has set up. Never paste tokens into commands or files.
- **Managed databases and backends** (Supabase, Neon, RDS, PlanetScale, Firebase). The provider patches the service. Check provider advisories and the client libraries the projects use.
- **Breached platforms.** When a platform the user uses reports a breach, it's a finding even without a CVE. List the secrets the user keeps there: env vars, API keys, deploy tokens, connected repositories. The fix is to rotate each secret and revoke the old one, not to patch. Mark it `fixed` only when every listed secret is rotated.

## Sites

- Status: `curl -sS -o /dev/null -w '%{http_code} %{ssl_verify_result}\n' https://<site>`. Compare with the expected status in the inventory. Redirects and 404s at an API root can be normal.
- TLS: `echo | openssl s_client -connect <host>:443 -servername <host> 2>/dev/null | openssl x509 -noout -issuer -enddate`. Flag expiry within 14 days, and issuers that browsers have distrusted.
- Headers: `curl -sI` shows `server`, `x-powered-by` and framework headers. These are worth matching against advisories, and worth suggesting the user hide.

## AI agents

- Agents run code with the user's permissions, so their CLIs, editor extensions and MCP servers are checked like any other app: versions against advisories.
- Agents can also send the user's own details to other sites, for example a contact email in a User-Agent or their name in a search. Scan their transcripts with `scripts/agent_privacy.py scan`, and remediate with the user. Both are in [agent-privacy.md](agent-privacy.md).

## Deployed vs fixed

A fix in the repo isn't a fix in production. For each project with an open item:

- Compare the deployed commit or version with the commit that contains the fix. Most platforms have a deployments listing, and panels show the running commit.
- Keep items at `fixing` until the deployed version has the fix and the service is healthy.

This is the most common reason a "fixed" vulnerability is still live.
