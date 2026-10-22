# Check results collected 2026-10-22 (treat these as the output of today's checks)

## osv-scanner, shop-web (package-lock.json)
- GHSA-f82v-jwr5-mffw, next 15.2.1, CVSS 9.1, fixed in 15.2.3
- GHSA-grv7-fg5c-xmjg, braces 3.0.2, CVSS 7.5, fixed in 3.0.3   <- osv now lists a fix
- GHSA-3h5v-q93c-6h6q, ws 8.13.0, CVSS 7.5, fixed in 8.17.1

## osv-scanner, api (requirements.txt)
- no high/critical findings

## trivy, python:3.12-slim (pulled 2026-10-22)
- CVE-2026-0001 glibc 2.36-9, CRITICAL, no fixed version

## web-1 (ssh)
- Ubuntu 24.04.3, kernel 6.8.0-90 running, newest installed 6.8.0-90
- /var/run/reboot-required: absent
- apt security updates pending: 0

## Mac
- softwareupdate: no updates
- node -v: v22.11.0

## Sites
- https://shop.example.com 200, TLS valid until 2027-01-10
- https://api.example.com 404, TLS valid until 2026-12-30

## Advisory feed items since 2026-10-21
1. https://nodejs.org/en/blog/vulnerability/october-2026-security-releases (2026-10-21) "Wednesday, October 21, 2026 Security Releases": high-severity fixes for Node.js 22.x (fixed in 22.23.4), 24.x and 26.x.
2. https://thehackernews.com/2026/10/example-old-story.html (2026-10-20) "Old story already seen"
3. CISA KEV CVE-2026-96656 (added 2026-10-20) "Plex Media Server External Control of File Name or Path"
4. https://www.postgresql.org/about/news/fossasia-pgday-2027-bangkok-9-march-cfp-open-3398/ (2026-10-20) "FOSSASIA PGDay 2027: Bangkok, 9 March - CFP Open"
5. https://github.com/vercel/next.js/security/advisories/GHSA-f82v-jwr5-mffw (republished 2026-10-21) "Authorization Bypass in Next.js Middleware"
