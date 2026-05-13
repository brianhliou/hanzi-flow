# Architecture

_Last updated: 2026-05-12_

## One-line shape

Next.js 15 + React 19 fully client-side adaptive Chinese-character learner; HSK 3.0 aligned; IndexedDB for state; pre-generated AWS Polly audio served as static assets.

## Components

- **Web** — Next.js 15 (static/hybrid) on Vercel
- **Client storage** — IndexedDB only
- **Audio assets** — pre-generated AWS Polly clips, served from static hosting

## Data flow

1. App loads HSK 3.0 character data from static JSON.
2. User progress persisted in IndexedDB on the client only.
3. Pre-generated audio clips fetched as static files.

## External dependencies

- Vercel (hosting)
- AWS Polly (one-time generation — no runtime cost)
- Domain: hanzi.brianhliou.com

## Notable choices

- 100% client-side — no server, no per-user storage cost, no auth.
- Maintenance posture — security patches only; no feature work without an approved sprint.
