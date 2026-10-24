# Check results collected 2026-10-24 (treat these as the output of today's checks)

## osv-scanner, api (requirements.txt)
- GHSA-75c5-xw7c-p5pm, pyjwt 2.8.0, CVSS 6.5, fixed in 2.10.1
  Advisory: a crafted token header skips signature verification. In api, pyjwt checks the token submitted to /login, before the user is authenticated.
- GHSA-59g5-xgcq-4qw3, python-multipart 0.0.9, CVSS 7.5, fixed in 0.0.18
  Advisory: denial of service by excessive logging when parsing a malformed multipart boundary.

## osv-scanner, api (scripts/requirements.txt)
- GHSA-9wx4-h78v-vm56, requests 2.31.0, CVSS 7.5, fixed in 2.32.0
  Advisory: certificate verification stays off for later requests in a Session after one request disables it.

## trivy, python:3.12-slim (pulled 2026-10-24)
- no high/critical findings

## Mac
- softwareupdate: no updates

## Sites
- https://api.example.com 404, TLS valid until 2026-12-30

## Advisory feed items since 2026-10-23
- none matching the keywords
