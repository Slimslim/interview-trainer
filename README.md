# Interview Trainer

A phone-first PWA for 3–10 minute sessions that rebuild hand-written Python and
interview reflexes for specific jobs: Anthropic **Forward Deployed Engineer** and
**Applied AI Architect, Industries**, with more jobs added as content packs.

You learn by doing. You write code that runs against hidden tests (real Python via
Pyodide, offline), fix bugs in an editor, order Parsons lines, and answer spoken
questions by recording or dictating. The optional Claude coach grades you against a
rubric and reads its feedback aloud.

- `docs/PLAN.md`: screens, data model, gating
- `docs/AUTHORING.md`: pack format and how to add a job
- `research/`: sourced research for each job (confirmed vs reported)
- `reports/`: test reports and screenshots

## Install on your iPhone
1. Open the app URL in **Safari**.
2. Tap **Share** (the square with an arrow) → **Add to Home Screen** → **Add**.
3. Open it once from the home screen while online and wait for "Python … ready ·
   works offline" on Home (about 15 MB is cached once). After that it works in
   airplane mode, including running Python.
4. Optional: **Settings → AI coach**: paste a Claude API key (console.anthropic.com).
   The key stays on the phone and is only ever sent to `api.anthropic.com`.

## Daily use
- **Start · 5 min**: one tap. It mixes items toward your weakest stage plus anything due for review.
- Chips switch tracks: **Comeback** (start here) → **FDE** / **AI Architect**.
- **Modes**: practise by stage, by item type, or a timed **full mock round**.
- **Review**: this week's mistakes grouped by pattern, with the lesson.
- **Stories**: your STAR story bank. Behavioral questions suggest which story fits.
- 🎙 on any spoken question records your answer (kept on the phone) and transcribes
  it. The keyboard's dictation mic works too.
- **Settings → Export/Import** moves your progress between devices as one JSON file.

## Run it locally
```bash
node tools/serve.mjs 8080      # then open http://localhost:8080
```

## Tests
```bash
bash tests/run-all.sh
```
Steps: build packs → validate content (schema, sources, 426 execution checks in
CPython) → the same checks in Pyodide → Playwright iPhone 15 e2e (screens in light and
dark, tap targets, horizontal scroll, editor with on-screen keys, offline, 4G timing,
persistence, export/import, coach with a mocked API). The self-review playthrough
(3 sessions with screenshots) is `node tests/playthrough.mjs`.

## Add a new job
1. Ask Claude Code: *"Run the research step for <job> → research/<slug>.md (sources
   table, every claim marked confirmed/reported with a link)"*.
2. Create `packs/<slug>/pack.json` with that job's interview stages and add the id to
   `packs/index.json`. Reuse existing items with a `reuse` rule
   (see `packs/anthropic-applied-ai-architect/pack.json`).
3. Write `content-src/<slug>/*.py` (format in `docs/AUTHORING.md`).
4. `python3 tools/build.py && python3 tools/validate.py --pack <slug> && node tools/validate-pyodide.mjs`
5. Deploy. The service worker picks up the new version on the next launch.

## Deploy
Live at **https://slimslim.github.io/interview-trainer/** (GitHub Pages, served from the
`gh-pages` branch). To publish changes:
```bash
bash tools/deploy.sh
```
It rebuilds the packs and `sw.js`, validates the content, and pushes `main` and `gh-pages`.
Installed copies pick up the new version on their next launch.
