# E2E report (2026-11-05T18:17Z, 393×659 iPhone 15 emulation)

**105/105 checks passed.**

| Metric | Value |
|---|---|
| First load, home usable (slow 4G, 150 ms RTT, 1.6 Mbps) | 1805 ms |
| Python ready after first load (background) | 17172 ms |
| Returning launch (service worker) | 70 ms |

## Mobile UX (83/83)

- ✅ light: no JS errors
- ✅ dark: no JS errors
- ✅ Quick start reaches first question — 1 tap(s)
- ✅ Comeback quick session opens with a hands-on code rep — Write code
- ✅ Editor: auto-indent + key bar reproduce the solution exactly — "def greet(name, n):\n    return f\"Hi {name}, you have {n} new messages\""
- ✅ Editor: typed code runs in Pyodide and passes — All 2 tests pass.
- ✅ Editor font ≥ 16px (no iOS zoom on focus) — 16px
- ✅ 76 per-screen layout checks (no horizontal scroll, tap targets ≥ 44 px) across light & dark — screenshots in reports/screenshots/

## Performance (2/2)

- ✅ First load (home usable) < 5 s on simulated 4G — 1805 ms
- ✅ Returning launch < 1 s (served by service worker, 4G throttled) — 70 ms

## Offline (4/4)

- ✅ App shell loads with network disabled
- ✅ Pyodide starts offline
- ✅ Python tests run offline — All 2 tests pass.
- ✅ Packs (design scenario) available offline

## Progress (7/7)

- ✅ XP persists across reload — 15 XP
- ✅ Streak persists
- ✅ Spaced repetition persists (miss due tomorrow, hit later) — bug due 2026-11-06, predict due 2026-11-06
- ✅ Readiness meter reflects attempts after reload — Coding (progressive levels) 48%
- ✅ Review groups this week's mistake by pattern — mutable default arg
- ✅ Export contains state, not the API key
- ✅ Import round-trips XP, streak, SRS and attempts

## AI coach (9/9)

- ✅ No key: role-play explains what's missing
- ✅ No key: role-play offers rubric self-grading
- ✅ No key: design explains + offers self-grading
- ✅ With key: design grading returns rubric feedback
- ✅ With key: role-play conversation + scoring work
- ✅ Sends required browser-access headers — model=claude-sonnet-5-5
- ✅ Role-play messages start with a user turn
- ✅ Key never sent anywhere except api.anthropic.com
- ✅ Key not stored in exportable state
