# Inventory (updated 2026-10-20)

## Device
- macOS 27.0, Homebrew, Python 3.12 via uv

## Projects
| Project | Path | Stack | Lockfiles | Deployed to | Production |
|---|---|---|---|---|---|
| api | ~/code/api | FastAPI, Python 3.12 | requirements.txt, scripts/requirements.txt, Dockerfile (python:3.12-slim) | Fly.io | yes |

## Threat notes
### api
- Untrusted input: public JSON API and the /login form
- Matters most: auth routes; out of scope: scripts/ (maintenance scripts run by hand on the laptop, never deployed)
- Severity: anything reachable before login is at least high; denial of service is medium

## Hosting
- Fly.io (Docker: we patch the base image)

## Sites
| URL | Host | Expected status |
|---|---|---|
| https://api.example.com | Fly.io | 404 at / (normal) |

## Keywords
FastAPI, Python, Fly.io, macOS
