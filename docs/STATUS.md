# Status

_Last updated: 2026-05-13_

**State:** maintenance — `mode = "Public side project"` per `~/projects/life-os/portfolio-repos.toml`.

## What's Active

Public Chinese-reading practice app at hanzi.brianhliou.com. Next.js 15 + React 19 + TypeScript + IndexedDB. Privacy-first / local-first — no backend, no tracking, works offline. HSK 3.0 aligned: levels 1–9, 3,000+ characters, 79,000+ sentences. NSS adaptive algorithm picks sentences based on per-character mastery scores.

Recent work: dependency hygiene only (Next.js security bump to 15.5.18, PostCSS audit alert, footer link fix). No feature pushes since the data pipeline matured.

## What's Next

Hold maintenance posture. Only touch for:
- Dependency security patches.
- Bug reports that reach the public surface (broken practice flow, audio failure, bad sentence selection).
- A specific request from a real user that demonstrates demand for a new feature.

Avoid feature-adds without evidence of use — see `docs/LESSONS_LEARNED.md` if it documents past scope drift, or check `KNOWN_ISSUES.md` first.

## Blockers

- None. App is functional and shipped; no live user count being tracked.
