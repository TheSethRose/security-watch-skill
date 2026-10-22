# Inventory (updated 2026-10-15)

## Device
- macOS 27.0, Homebrew, Node 22.11.0 via fnm

## Projects
| Project | Path | Stack | Lockfiles | Deployed to | Production |
|---|---|---|---|---|---|
| shop-web | ~/code/shop-web | Next.js 15.2.1, Node 22 | package-lock.json | Vercel | yes |
| api | ~/code/api | FastAPI, Python 3.12, Node 22.11 build step | requirements.txt, Dockerfile (python:3.12-slim) | Fly.io | yes |

## Servers
| Host | Access | OS | Runs |
|---|---|---|---|
| web-1 | ssh web-1 | Ubuntu 24.04 | Postgres 16 |

## Sites
| URL | Host | Expected status |
|---|---|---|
| https://shop.example.com | Vercel | 200 |
| https://api.example.com | Fly.io | 404 at / (normal) |

## Keywords
Next.js, Node.js, FastAPI, Python, Postgres, PostgreSQL, Ubuntu, Vercel, Fly.io, macOS, Chrome
