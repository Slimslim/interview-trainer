// One renderer per item type. Each returns a DOM node and calls
// ctx.finish(result) exactly once when the item is answered:
//   result = { correct, score (0–1), hints, ms, rating? }
// Rule everywhere: you act first (write, tap, speak); solutions and model
// answers appear only after you answer, use every hint, or ask for them.
import { h, md, pre, shuffle, toast, fmtTime } from "./ui.js";
import { codeEditor } from "./editor.js";
import * as py from "./python.js";
import * as store from "./store.js";
import * as coach from "./coach.js";
import { voiceInput, speak } from "./voice.js";

const now = () => performance.now();

function pyStatusLine() {
  const el = h("span.small.muted");
  py.onStatus(s => { el.textContent = s === "ready" ? "" : s === "error" ? "Python failed to load — reload the app." : "Python is loading in the background…"; });
  return el;
}

function testList(r) {
  if (r.error) return h("div.feedback.bad", h("b", "Your code raised an error"), pre(r.error));
  return h("ul.tests", r.tests.map(t => h("li",
    h("div", t.passed ? "✅ " : "❌ ", t.name.replace(/^test_/, "").replace(/_/g, " ")),
    !t.passed && t.message ? h("div.msg", t.message) : null)));
}
const testSummary = r => r.error ? `Error: ${r.error}` :
  r.tests.map(t => `${t.passed ? "PASS" : "FAIL"} ${t.name} ${t.message || ""}`).join("\n");

function lessonBlock({ lesson, ts, alternative, solution, solutionLabel = "Idiomatic version" }) {
  return h("div",
    lesson ? h("div.lesson", h("div.kicker", "Lesson"), md(lesson)) : null,
    ts ? h("div", h("div.kicker", "TypeScript ↔ Python"), md(ts.includes("`") ? ts : "In TS: `" + ts + "`")) : null,
    solution ? h("details", { open: true }, h("summary", solutionLabel), pre(solution)) : null,
    alternative ? h("details", h("summary", "Another approach"), md(alternative)) : null);
}

// ---------------------------------------------------------------- code task
// Shared by "code" items and each step of a progressive challenge.
export function codeTask(task, { draftKey, startCode, onPass, onGiveUp, timerMinutes, talkPrompts }) {
  const t0 = now();
  const mem = store.get().items[draftKey] || {};
  let code = mem.draft ?? startCode ?? task.starter ?? "";
  let hintsShown = 0, runs = 0, finished = false;
  const results = h("div");
  const hintBox = h("div");
  const after = h("div");
  const ed = codeEditor(code, {
    onChange: v => {
      code = v;
      const s = store.get();
      (s.items[draftKey] = s.items[draftKey] || { seen: 0 }).draft = v;
      clearTimeout(ed._t); ed._t = setTimeout(store.save, 400);
    },
  });

  const runBtn = h("button.primary", { type: "button" }, "▶ Run tests");
  const hintBtn = h("button", { type: "button" }, "💡 Hint 1/3");
  const solBtn = h("button.ghost", { type: "button" }, "Show solution");

  async function run() {
    runBtn.disabled = true;
    runBtn.textContent = py.isReady() ? "Running…" : "Loading Python…";
    const r = await py.runTests(code, task.tests);
    runs++;
    runBtn.disabled = false;
    runBtn.textContent = "▶ Run tests";
    const passed = r.tests.filter(t => t.passed).length;
    results.replaceChildren(
      r.ok ? h("div.feedback.good", h("b", `All ${r.tests.length} tests pass.`))
        : h("div.feedback.bad", r.error ? "Not yet — read the error bottom-up." : `${passed}/${r.tests.length} tests pass.`),
      testList(r),
      r.stdout ? h("details", h("summary", "Printed output"), pre(r.stdout)) : null);
    if (r.ok && !finished) {
      finished = true;
      const score = Math.max(0.3, 1 - 0.2 * hintsShown - 0.04 * Math.max(0, runs - 3));
      after.replaceChildren(
        lessonBlock({ ...task, solution: task.solution, solutionLabel: "Reference solution (compare with yours)" }),
        coachButton(task, () => code, true, () => testSummary(r)));
      onPass({ correct: true, score, hints: hintsShown, ms: now() - t0 });
    } else if (!r.ok && coach.hasKey()) {
      results.append(coachButton(task, () => code, false, () => testSummary(r)));
    }
    results.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function hint() {
    if (hintsShown >= 3) return;
    hintBox.append(h("div.feedback.info", h("b", `Hint ${hintsShown + 1}: `), md(task.hints[hintsShown])));
    hintsShown++;
    hintBtn.textContent = hintsShown < 3 ? `💡 Hint ${hintsShown + 1}/3` : "No more hints";
    hintBtn.disabled = hintsShown >= 3;
    if (hintsShown >= 3) solBtn.textContent = "Show solution";
  }

  function giveUp() {
    if (finished) return;
    if (hintsShown < 3 && !confirm("Show the solution? Try the hints first — this counts as a miss and the item comes back tomorrow.")) return;
    finished = true;
    after.replaceChildren(h("div.feedback.info", "Study it, then type it yourself — this item will come back for review."),
      lessonBlock({ ...task, solutionLabel: "Reference solution" }));
    onGiveUp({ correct: false, score: 0, hints: hintsShown, ms: now() - t0 });
  }

  runBtn.onclick = run;
  hintBtn.onclick = hint;
  solBtn.onclick = giveUp;

  // optional countdown + talk-aloud nudges
  let timerEl = null;
  if (timerMinutes && store.get().profile.timer) {
    timerEl = h("span.timer", fmtTime(timerMinutes * 60));
    const end = Date.now() + timerMinutes * 60000;
    const iv = setInterval(() => {
      if (!timerEl.isConnected) return clearInterval(iv);
      const left = (end - Date.now()) / 1000;
      timerEl.textContent = left > 0 ? fmtTime(left) : "time!";
      timerEl.classList.toggle("low", left < 60);
    }, 1000);
  }
  if (store.get().profile.talkAloud) {
    const prompts = talkPrompts?.length ? talkPrompts : ["Say what you're about to write and why.", "State the complexity out loud.", "Name one edge case you haven't handled.", "Explain your data structure choice in one sentence."];
    let i = 0;
    const iv = setInterval(() => {
      if (!ed.isConnected) return clearInterval(iv);
      if (!finished) toast("🗣 " + prompts[i++ % prompts.length], 4000);
    }, 90000);
  }

  return h("div.stack",
    h("div.row.spread", h("div.kicker", task.title || "Write code"), timerEl),
    h("div.prompt", md(task.prompt)),
    task.ts && store.get().profile.track === "comeback" ? h("details", h("summary", "How you'd write it in TypeScript"), md(task.ts.includes("`") ? task.ts : "`" + task.ts + "`")) : null,
    ed,
    h("div.row.wrap", runBtn, hintBtn, solBtn, pyStatusLine()),
    hintBox, results, after);
}

function coachButton(task, getCode, solved, getTests) {
  if (!coach.hasKey()) return null;
  const out = h("div");
  const b = h("button.ghost", { type: "button" }, solved ? "🧑‍🏫 Coach review" : "🧑‍🏫 Ask coach for a nudge");
  b.onclick = async () => {
    b.disabled = true; b.textContent = "Thinking…";
    try {
      const text = await coach.reviewCode({ prompt: task.prompt, code: getCode(), solved, tests: getTests() });
      out.replaceChildren(h("div.card", md(text)));
      speak(text);
    } catch (e) { out.replaceChildren(h("div.feedback.bad", e.message)); }
    b.disabled = false; b.textContent = solved ? "🧑‍🏫 Coach review" : "🧑‍🏫 Ask coach again";
  };
  return h("div", b, out);
}

// ---------------------------------------------------------------- players
export function renderCode(item, ctx) {
  return codeTask(item, {
    draftKey: item.id,
    onPass: ctx.finish, onGiveUp: ctx.finish,
    timerMinutes: ctx.mock ? null : (item.week >= 3 ? 4 : null),
  });
}

export function renderChallenge(item, ctx) {
  const s = store.get();
  const mem = s.items[item.id] = s.items[item.id] || { seen: 0 };
  let step = Math.min(mem.step || 0, item.steps.length - 1);
  const box = h("div");
  const stepsDone = [];

  function show() {
    const st = item.steps[step];
    const prevKey = `${item.id}#${step - 1}`;
    const prevCode = step > 0 ? (s.items[prevKey]?.draft ?? item.steps[step - 1].solution) : null;
    const header = h("div.row.wrap",
      item.steps.map((_, i) => h("span.pill", { style: i === step ? { background: "var(--accent)", color: "var(--accent-ink)" } : {} }, `Level ${i + 1}`)));
    const intro = step === 0 ? h("p.muted", item.summary) :
      h("div.feedback.info", "New requirement. Refactor your previous code — keep the earlier behaviour working.");
    const next = h("div");
    const onDone = res => {
      stepsDone.push(res);
      mem.step = res.correct ? step + 1 : step;
      store.save();
      const last = step >= item.steps.length - 1;
      const finishAll = () => {
        mem.step = mem.step >= item.steps.length ? 0 : mem.step;
        store.save();
        const n = stepsDone.length;
        ctx.finish({
          correct: stepsDone.every(r => r.correct), score: stepsDone.reduce((a, r) => a + r.score, 0) / n,
          hints: stepsDone.reduce((a, r) => a + r.hints, 0), ms: stepsDone.reduce((a, r) => a + r.ms, 0),
          steps: n,
        });
      };
      if (last || !res.correct || (ctx.quick && !ctx.mock)) {
        next.replaceChildren(
          !last && res.correct ? h("button.primary.block", { type: "button", onclick: () => { step++; show(); } }, `Keep going → Level ${step + 2}`) : null,
          h("button.block", { type: "button", style: { marginTop: "8px" }, onclick: finishAll }, last ? "Finish challenge" : "Stop here (resume next time)"));
      } else {
        next.replaceChildren(h("button.primary.block", { type: "button", onclick: () => { step++; show(); } }, `Next level → ${step + 2}/${item.steps.length}`));
      }
    };
    box.replaceChildren(header, intro, codeTask(st, {
      draftKey: `${item.id}#${step}`, startCode: st.starter ?? prevCode,
      onPass: onDone, onGiveUp: onDone, timerMinutes: st.minutes, talkPrompts: item.talkPrompts,
    }), next);
    window.scrollTo(0, 0);
  }
  show();
  return box;
}

export function renderBug(item, ctx) {
  const t0 = now();
  const lines = item.code.replace(/\n$/, "").split("\n");
  const fixedLines = item.fixed.replace(/\n$/, "").split("\n");
  let wrongTaps = 0, done = false, found = false, editLine = null, usedChoices = false, attempts = 0;
  const out = h("div");
  const list = h("div.codelines", { role: "list" });
  const actions = h("div.row.wrap");

  function finish(correct) {
    if (done) return;
    done = true;
    const score = correct ? Math.max(0.3, 1 - 0.2 * wrongTaps - (usedChoices ? 0.3 : 0) - 0.1 * Math.max(0, attempts - 1)) : 0;
    out.append(h("div.lesson", h("div.kicker", "Why"), md(item.explanation)),
      h("details", { open: !correct }, h("summary", "Fixed version"), pre(item.fixed)));
    ctx.finish({ correct, score, hints: wrongTaps, ms: now() - t0 });
  }

  function renderLines() {
    list.replaceChildren(...lines.map((src, i) => {
      const n = i + 1;
      if (found && n === item.bugLine && !done) {
        const inp = h("input", { type: "text", value: editLine ?? src, autocapitalize: "off", autocorrect: "off", spellcheck: false, "aria-label": `Edit line ${n}` });
        inp.addEventListener("input", () => { editLine = inp.value; });
        setTimeout(() => inp.focus(), 50);
        return h("div.codeline.right", h("span.ln", n), inp);
      }
      const b = h("button.codeline", { type: "button", "aria-label": `Line ${n}` }, h("span.ln", n), h("span.src", (done && n === item.bugLine) ? fixedLines[i] ?? src : src || " "));
      if (done && n === item.bugLine) b.classList.add("right");
      b.onclick = () => {
        if (found || done) return;
        if (n === item.bugLine) {
          found = true;
          out.replaceChildren(h("div.feedback.good", "Yes — that's the line. Now fix it in place and run the tests."));
          renderLines();
          renderActions();
        } else {
          wrongTaps++;
          b.classList.add("wrong");
          out.replaceChildren(h("div.feedback.bad", wrongTaps >= 3 ? "Look at the highlighted line." : "Not that one. Run the code in your head with the failing case."));
          if (wrongTaps >= 3) { found = true; renderLines(); renderActions(); }
        }
      };
      return b;
    }));
  }

  async function runFix() {
    const code = lines.map((l, i) => (i + 1 === item.bugLine ? (editLine ?? l) : l)).join("\n") + "\n";
    attempts++;
    out.replaceChildren(h("p.muted", py.isReady() ? "Running…" : "Loading Python…"));
    const r = await py.runTests(code, item.tests);
    out.replaceChildren(r.ok ? h("div.feedback.good", h("b", "Fixed — all tests pass.")) : h("div.feedback.bad", "Still failing."), testList(r));
    if (r.ok) { lines[item.bugLine - 1] = editLine; renderLines(); renderActions(); finish(true); }
  }

  function choices() {
    usedChoices = true;
    out.replaceChildren(h("div.choices", item.choices.map((c, i) => {
      const b = h("button.choice", { type: "button" }, c);
      b.onclick = () => {
        if (done) return;
        out.querySelectorAll(".choice").forEach((x, j) => j === item.answer && x.classList.add("right"));
        if (i !== item.answer) b.classList.add("wrong");
        finish(i === item.answer);
        renderLines();
        actions.replaceChildren();
      };
      return b;
    })));
  }

  function renderActions() {
    if (done) return actions.replaceChildren();
    actions.replaceChildren(
      found ? h("button.primary", { type: "button", onclick: runFix }, "▶ Run tests with my fix") : null,
      h("button.ghost", { type: "button", onclick: choices }, "Pick the fix from options"),
      h("button.ghost", { type: "button", onclick: () => { finish(false); renderLines(); renderActions(); } }, "Show answer"));
  }

  renderLines();
  renderActions();
  return h("div.stack", h("div.kicker", "Spot the bug — tap the broken line"), h("p", h("b", item.title)), list, actions, out, pyStatusLine());
}

export function renderPredict(item, ctx) {
  const t0 = now();
  let done = false;
  const bar = h("i", { style: { width: "100%" } });
  const out = h("div");
  const LIMIT = 20;
  const iv = setInterval(() => {
    const left = LIMIT - (now() - t0) / 1000;
    bar.style.width = `${Math.max(0, (left / LIMIT) * 100)}%`;
    if (left <= 0 || done || !bar.isConnected) clearInterval(iv);
  }, 250);
  const mono = item.kind !== "concept";
  const choiceEls = item.choices.map((c, i) => {
    const b = h(`button.choice${mono ? ".mono" : ""}`, { type: "button" }, c);
    b.onclick = () => {
      if (done) return;
      done = true;
      const ms = now() - t0;
      choiceEls[item.answer].classList.add("right");
      const correct = i === item.answer;
      if (!correct) b.classList.add("wrong");
      out.replaceChildren(h(`div.feedback.${correct ? "good" : "bad"}`, correct ? (ms < LIMIT * 1000 ? "Correct — fast." : "Correct.") : "Not quite."),
        h("div.lesson", md(item.explanation)), item.ts ? h("div", h("div.kicker", "TypeScript ↔ Python"), md(item.ts)) : null);
      ctx.finish({ correct, score: correct ? 1 : 0, ms });
    };
    return b;
  });
  return h("div.stack",
    h("div.kicker", item.kind === "complexity" ? "Complexity · 20 s" : item.kind === "concept" ? "Quick check · 20 s" : "Predict the output · 20 s"),
    h("div.countdown", bar),
    item.code ? pre(item.code) : null,
    h("p", h("b", item.question)),
    h("div.choices", choiceEls), out);
}

export function renderParsons(item, ctx) {
  const t0 = now();
  const indexed = item.lines.map((text, i) => ({ text, i }));
  let pool = shuffle(indexed);
  while (pool.length > 2 && pool.every((l, k) => l.i === k)) pool = shuffle(indexed);
  let answer = [], done = false, tries = 0;
  const poolEl = h("div.parsons-list"), ansEl = h("div.parsons-list.dropzone");
  const out = h("div");
  const check = h("button.primary.block", { type: "button", disabled: true }, "Check order");

  function draw() {
    const line = (l, from) => h("button.pline", {
      type: "button", onclick: () => {
        if (done) return;
        if (from === "pool") { pool = pool.filter(x => x !== l); answer.push(l); }
        else { answer = answer.filter(x => x !== l); pool.push(l); }
        draw();
      },
    }, from === "ans" ? h("span.n", answer.indexOf(l) + 1) : null, l.text.replace(/^ +/, m => " ".repeat(m.length)));
    poolEl.replaceChildren(...pool.map(l => line(l, "pool")));
    ansEl.replaceChildren(...(answer.length ? answer.map(l => line(l, "ans")) : [h("p.muted.small.center", "Tap lines in the order they should run")]));
    check.disabled = pool.length > 0 || done;
  }

  check.onclick = async () => {
    tries++;
    const code = answer.map(l => l.text).join("\n") + "\n";
    let ok = answer.every((l, k) => l.i === k);
    let r = null;
    if (!ok && py.isReady()) { r = await py.runTests(code, item.tests); ok = r.ok; }
    if (ok) {
      done = true;
      out.replaceChildren(h("div.feedback.good", "Correct order" + (answer.every((l, k) => l.i === k) ? "." : " — a different valid order, tests pass.")),
        h("div.lesson", md(item.lesson)));
      draw();
      ctx.finish({ correct: true, score: Math.max(0.4, 1 - 0.25 * (tries - 1)), hints: tries - 1, ms: now() - t0 });
    } else {
      const firstWrong = answer.findIndex((l, k) => l.i !== k);
      out.replaceChildren(h("div.feedback.bad", `Not yet. Line ${firstWrong + 1} is the first one out of place.`), r ? testList(r) : null,
        tries >= 2 ? h("button.ghost", { type: "button", onclick: reveal }, "Show the answer") : null);
    }
  };
  function reveal() {
    done = true;
    answer = indexed.slice(); pool = [];
    draw();
    out.replaceChildren(h("div.lesson", md(item.lesson)));
    ctx.finish({ correct: false, score: 0, hints: tries, ms: now() - t0 });
  }
  draw();
  return h("div.stack", h("div.kicker", "Parsons puzzle"), h("p", h("b", item.title)), md(item.prompt),
    h("div.kicker", "Your program"), ansEl, check, h("div.kicker", "Lines"), poolEl, out);
}

export function renderFlashcard(item, ctx) {
  const t0 = now();
  const back = h("div.hidden", h("hr"), md(item.back), item.example ? pre(item.example) : null);
  const rate = h("div.rate.hidden",
    [["Again", 1], ["Hard", 3], ["Good", 4], ["Easy", 5]].map(([label, q]) =>
      h("button", { type: "button", onclick: () => { rate.querySelectorAll("button").forEach(b => (b.disabled = true)); ctx.finish({ rating: q, correct: q >= 3, score: q / 5, ms: now() - t0 }); } }, label)));
  const reveal = h("button.primary.block", { type: "button" }, "Show answer");
  reveal.onclick = () => { back.classList.remove("hidden"); rate.classList.remove("hidden"); reveal.classList.add("hidden"); };
  return h("div.stack", h("div.kicker", "Flashcard — answer out loud first"),
    h("div.card.flash", md(item.front), back), reveal, rate);
}

// ------------------------------------------------- spoken / written answers
function answerBox(item, placeholder) {
  const ta = h("textarea.answer", { placeholder, "aria-label": "Your answer" });
  const drafts = store.get().items[item.id]?.draft;
  if (typeof drafts === "string") ta.value = drafts;
  ta.addEventListener("input", () => {
    const s = store.get();
    (s.items[item.id] = s.items[item.id] || { seen: 0 }).draft = ta.value;
    clearTimeout(ta._t); ta._t = setTimeout(store.save, 400);
  });
  return { ta, voice: voiceInput(ta, item.id) };
}

function saveAnswer(item, text, score, feedback) {
  const s = store.get();
  const list = s.answers[item.id] = s.answers[item.id] || [];
  list.unshift({ t: Date.now(), text, score: +score.toFixed(2), feedback });
  s.answers[item.id] = list.slice(0, 5);
  if (s.items[item.id]) s.items[item.id].draft = "";
  store.save();
}

// Rubric grading: Claude if a key is set, otherwise a self-check list.
function gradeFlow(item, { prompt, rubric, getAnswer, after, ctx, t0, extra }) {
  const out = h("div");
  const coachBtn = h("button.primary", { type: "button" }, "🧑‍🏫 Grade with coach");
  const selfBtn = h("button", { type: "button" }, "✓ Grade myself");
  let done = false;

  function complete(score, feedback) {
    if (done) return;
    done = true;
    coachBtn.disabled = selfBtn.disabled = true;
    saveAnswer(item, getAnswer(), score, feedback);
    if (after) out.append(after());
    ctx.finish({ correct: score >= 0.7, score, ms: now() - t0 });
  }

  coachBtn.onclick = async () => {
    if (!getAnswer().trim()) return toast("Answer first — record, dictate or type.");
    coachBtn.disabled = true; coachBtn.textContent = "Grading…";
    try {
      const g = await coach.gradeRubric({ prompt, answer: getAnswer(), rubric, extra });
      const score = coach.rubricScore(rubric, g.scores);
      out.replaceChildren(h("div.card",
        h("div.row.spread", h("b", "Coach feedback"), h("span.pill", `${Math.round(score * 100)}%`)),
        h("ul.tests", g.scores.map(s => h("li", h("div", ["❌", "🟡", "✅"][Math.max(0, Math.min(2, +s.score || 0))], " ", h("b", s.criterion)), h("div.msg", s.note || "")))),
        md(g.summary || ""), g.next ? h("p", h("b", "Practise next: "), g.next) : null,
        h("button.ghost", { type: "button", onclick: () => speak(`${g.summary} ${g.next || ""}`, { force: true }) }, "🔊 Play feedback")));
      speak(`${g.summary || ""} ${g.next ? "Practise next: " + g.next : ""}`);
      complete(score, g.summary);
    } catch (e) {
      out.replaceChildren(h("div.feedback.bad", e.message + " — you can grade yourself instead."));
      coachBtn.disabled = false; coachBtn.textContent = "🧑‍🏫 Grade with coach";
    }
  };

  selfBtn.onclick = () => {
    if (!getAnswer().trim() && !confirm("No answer recorded or typed. Grade anyway?")) return;
    const boxes = rubric.map(r => h("input", { type: "checkbox" }));
    out.replaceChildren(h("div.card.rubric",
      h("b", "Tick what your answer actually covered"),
      rubric.map((r, i) => h("label", boxes[i], h("span", h("b", r.criterion), h("br"), h("span.small.muted", r.lookFor)))),
      h("button.primary.block", {
        type: "button", style: { marginTop: "10px" }, onclick: e => {
          e.target.disabled = true;
          let tot = 0, got = 0;
          rubric.forEach((r, i) => { tot += r.weight || 1; if (boxes[i].checked) got += r.weight || 1; });
          out.append(h("div.feedback.info", `Self-score ${Math.round((100 * got) / tot)}%`));
          complete(got / tot, "self-graded");
        },
      }, "Done")));
  };

  const keyNote = coach.hasKey() ? null : h("p.small.muted", "No API key: grade yourself against the rubric. Add a key in Settings for spoken AI feedback.");
  if (!coach.hasKey()) coachBtn.classList.add("hidden");
  return h("div", h("div.row.wrap", coachBtn, selfBtn), keyNote, out);
}

const STAR = [
  { criterion: "Situation & Task", lookFor: "Brief, concrete context: who, where, what was at stake, your responsibility.", weight: 1 },
  { criterion: "Action (I, not we)", lookFor: "Specific steps you personally took and why; tradeoffs considered.", weight: 1.5 },
  { criterion: "Result with numbers", lookFor: "Measurable outcome (time, money, adoption, error rate) or honest outcome if it failed.", weight: 1 },
  { criterion: "Honest reflection", lookFor: "What you learned or would do differently; no spin, owns mistakes.", weight: 1 },
  { criterion: "Answered the actual question", lookFor: "Stays on the question, under ~2 minutes, clear structure.", weight: 1 },
];

export function renderBehavioral(item, ctx) {
  const t0 = now();
  const { ta, voice } = answerBox(item, "Record, dictate or type your answer (aim for ~2 minutes spoken).");
  const rubric = [...STAR, ...item.lookFor.map(l => ({ criterion: l.length > 60 ? l.slice(0, 57) + "…" : l, lookFor: l, weight: 1 }))];
  const storyOut = h("div");
  const storyBtn = h("button.ghost", { type: "button" }, "📚 Which of my stories fits?");
  storyBtn.onclick = async () => {
    const stories = store.get().stories;
    if (!stories.length) return storyOut.replaceChildren(h("p.small.muted", "Your story bank is empty — add stories from Home → Stories."));
    if (coach.hasKey()) {
      storyBtn.disabled = true;
      try {
        const s = await coach.suggestStory(item.question, stories);
        const st = stories.find(x => x.id === s?.id);
        storyOut.replaceChildren(st ? h("div.card", h("b", st.title), h("p", s.why), h("p.small", h("b", "Angle: "), s.angle)) : h("p.muted", "No clear match — consider writing a new story."));
      } catch (e) { storyOut.replaceChildren(h("div.feedback.bad", e.message)); }
      storyBtn.disabled = false;
    } else {
      // offline: rank by shared words between the question and each story
      const words = new Set(item.question.toLowerCase().match(/[a-z]{4,}/g) || []);
      const ranked = stories.map(st => ({ st, n: (JSON.stringify(st).toLowerCase().match(/[a-z]{4,}/g) || []).filter(w => words.has(w)).length + (st.tags || []).filter(t => item.tags.includes(t)).length * 3 }))
        .sort((a, b) => b.n - a.n).slice(0, 2);
      storyOut.replaceChildren(...ranked.map(({ st }) => h("div.card", h("b", st.title), h("p.small", st.situation))));
    }
  };
  return h("div.stack",
    h("div.kicker", "Behavioral — answer out loud"),
    h("p.prompt", h("b", item.question)),
    item.source ? h("span.pill", "Reported question") : null,
    storyBtn, storyOut,
    voice, ta,
    gradeFlow(item, {
      prompt: item.question, rubric, getAnswer: () => ta.value, ctx, t0,
      extra: item.value ? `Company value probed: ${item.value}` : "",
      after: () => h("div", item.followUps?.length ? h("div.card", h("b", "Likely follow-ups"), h("ul", item.followUps.map(f => h("li", f)))) : null),
    }));
}

export function renderDesign(item, ctx) {
  const t0 = now();
  const { ta, voice } = answerBox(item, "Talk it through: requirements → architecture → evals → guardrails → human checkpoints → security → rollout.");
  return h("div.stack",
    h("div.kicker", `Design scenario · ~${item.minutes || 10} min`),
    h("p", h("b", item.title)), md(item.prompt),
    h("details", h("summary", "Structure to follow"), h("ol", item.rubric.map(r => h("li", r.criterion)))),
    voice, ta,
    gradeFlow(item, {
      prompt: item.prompt, rubric: item.rubric, getAnswer: () => ta.value, ctx, t0,
      after: () => h("details", { open: true }, h("summary", "Strong answer outline"), md(item.outline)),
    }));
}

export function renderRoleplay(item, ctx) {
  const t0 = now();
  const root = h("div.stack", h("div.kicker", "Customer role-play"), h("p", h("b", item.title)), h("div.card", md(item.brief)));
  if (!coach.hasKey()) {
    // Offline drill: write your discovery questions, then reveal what the customer was hiding.
    const { ta, voice } = answerBox(item, "List (or say) the discovery questions you'd ask, in order.");
    root.append(
      h("div.feedback.info", "Live role-play needs the AI coach (add a Claude API key in Settings). Offline drill: plan your discovery, then check it against what the customer was hiding."),
      h("p", h("b", "Their opening line: "), `“${item.opening}”`), voice, ta,
      gradeFlow(item, {
        prompt: item.brief, rubric: item.rubric, getAnswer: () => ta.value, ctx, t0,
        after: () => h("div.card", h("b", "What they would have revealed if asked"), h("ul", item.hiddenFacts.map(f => h("li", f)))),
      }));
    return root;
  }
  const transcript = [{ role: "assistant", content: item.opening }];
  const chat = h("div.chat");
  const system = `You are role-playing a customer in a mock interview for an Anthropic customer-facing engineering role.
PERSONA: ${item.persona}
HIDDEN FACTS (reveal each one ONLY when the candidate asks a question that would naturally surface it; never volunteer them all):
${item.hiddenFacts.map(f => "- " + f).join("\n")}
Rules: stay in character; reply in 1–3 short spoken sentences; no markdown; push back if they propose a solution before understanding your situation.`;
  const draw = () => {
    chat.replaceChildren(...transcript.map(m => h(`div.bubble.${m.role === "user" ? "me" : "them"}`, m.content)));
    chat.lastChild?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  };
  draw();
  speak(item.opening);
  const { ta, voice } = answerBox(item, "Your turn — record or type, then Send.");
  const send = h("button.primary", { type: "button" }, "Send");
  const end = h("button", { type: "button" }, "End & score");
  const out = h("div");
  send.onclick = async () => {
    const text = ta.value.trim();
    if (!text) return;
    transcript.push({ role: "user", content: text });
    ta.value = "";
    draw();
    send.disabled = true; send.textContent = "…";
    try {
      // The API wants the first message from "user", so a stage direction precedes the persona's opening line.
      const messages = [{ role: "user", content: "(The meeting starts. Say your opening line.)" }, ...transcript];
      const reply = await coach.ask({ system, messages, maxTokens: 300 });
      transcript.push({ role: "assistant", content: reply });
      draw();
      speak(reply);
    } catch (e) { toast(e.message); transcript.pop(); ta.value = text; draw(); }
    send.disabled = false; send.textContent = "Send";
  };
  end.onclick = () => {
    end.disabled = send.disabled = true;
    const convo = transcript.map(m => `${m.role === "user" ? "CANDIDATE" : "CUSTOMER"}: ${m.content}`).join("\n");
    out.replaceChildren(gradeFlow(item, {
      prompt: `Discovery role-play. Brief: ${item.brief}\nHidden facts the candidate should have uncovered: ${item.hiddenFacts.join("; ")}`,
      rubric: item.rubric, getAnswer: () => convo, ctx, t0,
      after: () => h("div.card", h("b", "Hidden facts"), h("ul", item.hiddenFacts.map(f => h("li", f)))),
    }));
  };
  root.append(chat, voice, ta, h("div.row", send, end), out);
  return root;
}

export const PLAYERS = {
  code: renderCode, challenge: renderChallenge, bug: renderBug, predict: renderPredict, parsons: renderParsons,
  flashcard: renderFlashcard, behavioral: renderBehavioral, design: renderDesign, roleplay: renderRoleplay,
};
