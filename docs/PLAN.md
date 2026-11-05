# Interview Trainer — one-page plan

**Goal:** a phone-first PWA for 3–10 minute sessions that rebuild hand-written Python
and interview reflexes for specific jobs (first: Anthropic FDE, Applied AI Architect).
Learn by doing: you write code that runs against hidden tests, and you answer
spoken questions by recording or dictating.

## Screens
| Screen | What it does |
|---|---|
| Home | Level/XP, 🔥 streak, track chips (Comeback · FDE · Architect), **Quick start** (1 tap → first question), readiness meter per interview stage, Comeback week gate |
| Session | One item at a time: code, challenge step, bug, predict, Parsons, flashcard, design, role-play, behavioral. Progress bar, optional countdown, talk-aloud nudges |
| Summary | XP earned, accuracy, streak, what to review |
| Modes | By stage, by item type, full mock round (timed, one stage end to end), placement quiz |
| Review | This week's mistakes grouped by pattern, with the lesson and a "drill this" button |
| Stories | STAR story bank (local only); coach suggests the best story for a question |
| Settings | Claude API key (device only), model, theme, timer, voice feedback, session length, export/import |

## Architecture
- Static site, no build step for the app: `index.html` + ES modules in `app/`.
- `app/py-worker.js` runs Pyodide (vendored in `vendor/pyodide/`) in a Web Worker;
  `app/harness.py` runs learner code + hidden tests (the same harness the CPython
  validator uses). A runaway loop is stopped by terminating the worker.
- `sw.js` precaches the shell, packs and Pyodide → fully offline after first load.
- Optional coach: browser → `api.anthropic.com/v1/messages` directly with the key
  from Settings (`anthropic-dangerous-direct-browser-access: true`). No other server.
- Voice: MediaRecorder (recordings kept in IndexedDB on the device), live
  transcription via the Web Speech API when available (else iOS keyboard dictation),
  feedback read aloud with speechSynthesis.

## Data model (localStorage `it.v1`, all wrapped in try/catch)
```
profile   { track, theme, timer, talkAloud, voice, minutes, skipGates, model }
xp, streak { count, best, lastDay }, days { "YYYY-MM-DD": { xp, items } }
attempts  [ { id, pack, stage, type, pattern, correct, score, ms, hints, day } ]  (last 3000)
srs       { itemId: { ef, interval, reps, due, lapses } }      SM-2
items     { itemId: { seen, last, draft, step } }               drafts, challenge step
comeback  { week }                                              highest unlocked week
stories   [ { id, title, situation, task, action, result, reflection, tags } ]
answers   { itemId: [ { t, text, score, feedback } ] }
```
The API key is stored separately (`it.apikey`) and is never exported.

## Pack format
See `docs/AUTHORING.md`. `packs/<slug>/pack.json` (stages, files, reuse rules) +
`packs/<slug>/<type>.json`, generated from `content-src/<slug>/*.py`, validated by
`tools/validate.py` (CPython) and `tools/validate-pyodide.mjs` (Pyodide).

## Gating
Comeback week N unlocks at 80 % of week N−1 items correct (latest attempt), or by
placement quiz (8/10). Job-pack coding items unlock as you go: predict after week 1,
bugs + Parsons after week 2, progressive challenges after week 3. Non-coding prep
(flashcards, design, role-play, behavioral) is always open. Settings → "Skip gates".
