# Authoring content packs

Content lives in `packs/<pack-id>/` as versioned JSON, generated from Python
sources in `content-src/<pack-id>/<file>.py` (code is far easier to write in
Python triple-quoted strings than in JSON). Each source module defines
`ITEMS = [...]`; `python3 tools/build_packs.py <pack-id>` writes
`packs/<pack-id>/<file>.json` (underscores become hyphens).

```
packs/index.json                 list of pack ids shown in the app
packs/<id>/pack.json             manifest: stages, files, version, research link, reuse rules
packs/<id>/<file>.json           {"version": "...", "items": [...]}   (generated)
content-src/<id>/<file>.py       ITEMS = [...]                         (you edit this)
schema/pack.schema.json          JSON schema for both
```

Use `from _helpers import code, lines` — `code('''...''')` dedents a block and
ends it with one newline; `lines('''...''')` gives a list of lines for Parsons.

## Common fields (every item)
| field | |
|---|---|
| `id` | globally unique, lowercase-kebab, prefixed by pack (e.g. `fde-bug-retry-429`, `cb-w2-counter`) |
| `type` | `code`, `challenge`, `bug`, `predict`, `parsons`, `flashcard`, `design`, `roleplay`, `behavioral` |
| `stage` | one of the pack's stage ids |
| `difficulty` | 1 easy, 2 medium, 3 hard |
| `tags` | free tags, e.g. `["dict", "hashing"]` |
| `pattern` | the one pattern/concept the item drills; the Review screen groups mistakes by it |
| `week` | Comeback only: 1–4 |
| `source` | optional: research source id (e.g. `S3`) when the item is based on a reported question |

## Tests (code, challenge, bug, parsons)
`tests` is Python source executed **after** the learner's code in the same
namespace. Every top-level `def test_*()` (or `async def test_*()`) is one test.
Use plain `assert` with a helpful message: `assert f(2) == 4, "f(2) should be 4"`.
`captured_output` holds everything the learner's code printed (use it for
print-based exercises). Learner code runs with `__name__ == "__solution__"`,
so `if __name__ == "__main__":` blocks don't run. Tests must be deterministic,
fast (<1 s), offline (no network, no real files outside `/tmp`, no `time.sleep`
over 0.05 s — inject a fake `sleep`/clock instead), and use only the standard library.

The validator enforces: reference solution passes every test, the starter fails
at least one, buggy code fails and fixed code passes, Parsons lines in order pass,
and predict-the-output code prints exactly the marked choice.

## Item types

**code** — single exercise (Comeback "type the line" items and small problems).
`title, prompt (markdown, short), starter, tests, hints[3] (nudge → near-answer),
solution, lesson (the idiom/method, 1–3 sentences), alternative? (another approach),
ts? (the TypeScript equivalent, shown as "in TS you'd write X")`.
Starter is usually a function stub with `pass` (fails the tests).

**challenge** — progressive coding problem, 3–4 `steps`. Each step:
`title, prompt, tests, hints[3], solution, lesson, alternative?, minutes?, starter?`.
Step 1 needs `starter`. Later steps normally omit `starter`: the learner keeps
their own code from the previous step, and the validator checks that the previous
step's reference solution FAILS the new tests (so each step really forces a change).
Item-level: `title, summary, talkPrompts[]` (things to say out loud while coding).

**bug** — `title, code (≤ 25 lines, exactly one bug), bugLine (1-based line number of
the bug in code), fixed (whole corrected snippet, same line count preferred), tests,
choices[3–4] (candidate fix descriptions), answer (index of correct fix), explanation`.

**predict** — `kind` = `output` (code must print exactly `choices[answer]`; if it
raises, the answer must contain the exception name, e.g. "KeyError"), `complexity`
or `concept` (not executed). `code?, question, choices[2–4], answer, explanation, ts?`.
Reflex items: should be answerable in ~20 seconds.

**parsons** — `title, prompt, lines (correct order, indentation included, all
lines unique — add a trailing comment to disambiguate duplicates), tests, lesson`.
The app shuffles the lines; any order that passes the tests is accepted.
Keep to 5–10 lines.

**flashcard** — `front, back, example?` (spaced repetition).

**design** — `title, prompt, rubric[{criterion, lookFor, weight?}], outline (a strong
answer's outline), minutes?`. Rubric criteria: requirements, architecture, evals,
guardrails, human checkpoints, security, rollout.

**roleplay** — `title, persona (who Claude plays), brief (what the learner is told),
opening (persona's first line), hiddenFacts[] (revealed only if the learner asks the
right questions), rubric[]`.

**behavioral** — `question, lookFor[], value? (which company value it probes),
followUps[]`.

## Adding a new job pack
1. Run the research step for the job → `research/<job-slug>.md` (sources table with
   `| S1 | title | url | date | confirmed/reported |`, every claim cites `[S#]`).
2. Create `packs/<job-slug>/pack.json` with the interview stages from the research
   and the list of files; add the id to `packs/index.json`.
3. Add `content-src/<job-slug>/*.py`. To reuse another pack's items, add a `reuse`
   rule in pack.json: `{"pack": "anthropic-fde", "types": ["challenge", "bug"],
   "stageMap": {"coding": "technical"}}`.
4. `python3 tools/build_packs.py <job-slug> && python3 tools/validate.py && node tools/validate-pyodide.mjs`
