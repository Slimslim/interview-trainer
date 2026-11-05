# Final report — definition of done

Run: `bash tests/run-all.sh` (2026-11-05). Details: `reports/e2e-report.md`, screenshots in
`reports/screenshots/` (light + dark), self-review screenshots in `reports/playthrough/`.

| # | Check | Result |
|---|---|---|
| 1 | Content validity | ✅ 420 items, schema-valid; 426 execution checks pass in **CPython 3.13** and **Pyodide 314.0.7** (reference solutions pass, starters fail, each challenge level's previous solution fails the new tests, buggy snippets fail / fixes pass, Parsons orders run, predict outputs match); both research files: every confirmed/reported claim cites a defined source with URL |
| 2 | Mobile UX (iPhone 15) | ✅ 21 screens × light/dark screenshotted; no horizontal scroll; every tap target ≥ 44 px; editor typed with the on-screen key bar + auto-indent reproduces and passes a solution; Quick start → first question in **1 tap** |
| 3 | Offline | ✅ network disabled after first load: shell, packs and **Python tests** all work |
| 4 | Performance | ✅ first load (slow 4G: 150 ms RTT, 1.6 Mbps) home usable in **~1.8 s**; Python ready in the background ~17 s; returning launch **~70 ms** |
| 5 | Progress | ✅ XP, streak, SM-2 schedule, readiness and Review persist across reload; export → import on a fresh device round-trips |
| 6 | AI coach | ✅ with key: design grading + live role-play + scoring (API mocked); required headers sent; the key never goes anywhere but api.anthropic.com and is not in exports. Without key: screens explain what's missing and offer rubric self-grading |
| 7 | Self-review | ✅ 3 full sessions played (Comeback 5 min, FDE 10 min, coding mock round); 5 friction points fixed (below) |

## Content counts
| Pack | Items |
|---|---|
| Comeback (4 weeks) | 152 — 101 write-code, 33 predict, 10 bug, 8 Parsons (W1 39 · W2 41 · W3 33 · W4 39) |
| Anthropic FDE | 218 — 9 progressive challenges (36 levels), 28 spot-the-bug (15 LLM-integration), 50 predict, 16 Parsons, 79 flashcards, 7 design, 5 role-play, 24 behavioral |
| Applied AI Architect | 50 own (5 design, 4 role-play, 17 behavioral, 24 flashcards) + reuses all FDE coding/design/values items |

## Self-review: the 5 most annoying friction points (all fixed)
1. **Sessions were mostly multiple choice.** A 5-min Comeback session had 1 code item out of 8; a 10-min FDE session had no coding at all. → ~70 % of each session is now hands-on (code, bug-fix, Parsons, a challenge level), every job-track session includes coding, and tiny week-1/2 reps are budgeted at ~1 min so more fit.
2. **After passing a challenge level the next step was buried** below tests, lesson and solution, and you earned nothing until the whole challenge ended. → The sticky thumb bar becomes **Next level → / Stop here**, and every level awards XP and is scheduled for review.
3. **Spot-the-bug only allowed editing one line**, so two-line fixes (e.g. mutable default → `None` + `if`) were impossible. → Tapping the right line opens the whole snippet in the code editor with the caret on that line.
4. **Run tests was far from the keyboard** (fixed 220 px editor + key bar). → ▶ key on the symbol bar runs tests without closing the keyboard; the editor grows with your code.
5. **Visual noise:** XP toast covered results and leaked onto the next screen, expandable sections looked like headings, rubric lines were duplicated, a stray "null" appeared. → Toast moved to the top and cleared on navigation, ▸ disclosure markers, de-duplicated rubric, null-safe rendering (and an e2e check that fails on stray `null`/`[object`).

## Known limits
- Research: Greenhouse postings and third-party prep sites were blocked from this environment, so posting text and reported questions come from search snippets (flagged in each research file's caveats). Worth re-reading the live postings.
- Live transcription uses the browser's Web Speech API; if iOS doesn't offer it in home-screen mode, the 🎙 button still records and the keyboard mic dictates.
- Threads aren't available in Pyodide, so concurrency is taught in lessons/flashcards rather than executed.
