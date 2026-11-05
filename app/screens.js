// All screens. Navigation is hash-based (#home, #modes, …) so the iOS back
// gesture and reloads behave; a running session lives in memory only.
import { h, mount, md, toast, fmtTime, download } from "./ui.js";
import * as store from "./store.js";
import * as content from "./content.js";
import * as progress from "./progress.js";
import * as sessions from "./session.js";
import * as py from "./python.js";
import * as coach from "./coach.js";
import { PLAYERS } from "./players.js";
import { voiceInput, stopSpeaking } from "./voice.js";

const S = () => store.get();
const nav = hash => { location.hash = hash; };
const back = (label = "‹ Home", to = "#home") => h("button.ghost", { type: "button", onclick: () => nav(to), style: { paddingLeft: 0 } }, label);

function header() {
  const s = S();
  const lv = progress.levelInfo(s.xp);
  return h("div.stack",
    h("div.row.spread",
      h("div", h("div.kicker", "Interview Trainer"), h("div.stat", `Level ${lv.level}`, h("span.muted.small", `  ${s.xp} XP`))),
      h("div.stats", h("span.stat", { title: "Daily streak", "aria-label": `Streak ${progress.streakAlive()} days` }, `🔥 ${progress.streakAlive()}`))),
    h("div.xpbar", { "aria-label": "XP to next level" }, h("i", { style: { width: `${Math.round((100 * lv.into) / lv.span)}%` } })));
}

function trackChips() {
  const s = S();
  const tracks = [{ id: "comeback", label: "Comeback" }, ...content.allPacks().filter(p => p.manifest.kind === "job")
    .map(p => ({ id: p.id, label: p.id === "anthropic-fde" ? "FDE" : p.id === "anthropic-applied-ai-architect" ? "AI Architect" : p.manifest.title }))];
  return h("div.chips", { role: "group", "aria-label": "Track" }, tracks.map(t => h("button.chip", {
    type: "button", "aria-pressed": String(s.profile.track === t.id),
    onclick: () => { s.profile.track = t.id; if (t.id !== "comeback") s.profile.jobPack = t.id; store.save(); home(); },
  }, t.label)));
}

// ------------------------------------------------------------------ home
export function home() {
  const s = S();
  const pv = sessions.quickPreview();
  const quick = h("button.primary.big.block", { type: "button", id: "quick-start", onclick: startQuick },
    `Start · ${s.profile.minutes} min`,
    h("small", pv.due ? `${pv.due} due for review · mixed reps` : "Mixed reps, weighted to your weakest area"));
  const minutes = h("div.chips", { role: "group", "aria-label": "Session length" }, [3, 5, 10].map(m => h("button.chip", {
    type: "button", "aria-pressed": String(s.profile.minutes === m), onclick: () => { s.profile.minutes = m; store.save(); home(); },
  }, `${m} min`)));
  const pyLine = h("p.small.muted");
  py.onStatus(st => { pyLine.textContent = st === "ready" ? `Python ${py.pyVersion()} ready · works offline` : st === "error" ? "Python failed to load" : "Loading Python in the background…"; });

  let body;
  if (s.profile.track === "comeback") {
    const unlocked = Math.min(5, s.comeback.week);
    body = h("div",
      h("h2", "Comeback track"),
      h("p.small.muted", "Rebuild hand-written Python. Each week unlocks at 80 % correct — or test out with a placement quiz."),
      [1, 2, 3, 4].map(w => {
        const st = progress.weekStats(w);
        const open = w <= unlocked || s.profile.skipGates;
        const title = content.getPack("comeback")?.manifest.stages[w - 1]?.title || `Week ${w}`;
        return h(`div.card${open ? "" : ".lock"}`,
          h("div.row.spread", h("b", title), h("span.small.muted", open ? `${st.correct}/${st.total} correct` : "🔒")),
          h("div.meter.good", { style: { margin: "8px 0" } }, h("i", { style: { width: `${Math.round(st.pct * 100)}%` } })),
          h("div.row.wrap",
            open ? h("button", { type: "button", onclick: () => startSession(sessions.drillSession(content.getPack("comeback").items.filter(i => i.week === w && !S().items[i.id]?.last).slice(0, 8).map(i => i.id), title)) }, "Practise") : null,
            !open || (w === unlocked && w < 5) ? h("button.ghost", { type: "button", onclick: () => startSession(sessions.placementSession(w)) }, "Placement quiz") : null));
      }),
      unlocked > 4 ? h("div.feedback.good", "Comeback complete — switch to a job track above.") : null);
  } else {
    const r = progress.readiness(s.profile.track);
    body = h("div.readiness",
      h("h2", "Readiness by interview stage"),
      r.map(st => h("button.list-btn", { type: "button", onclick: () => startSession(sessions.stageSession(s.profile.track, st.id)), style: { display: "block" } },
        h("div.row.spread", h("span", st.title), h("b", `${st.value}%`)),
        h("div.meter", { style: { marginTop: "6px" } }, h("i", { style: { width: `${st.value}%` } })))),
      h("p.small.muted", "Tap a stage to practise it. Readiness = recent accuracy × coverage."));
  }

  const mistakes = progress.mistakesByPattern().length;
  mount(
    header(),
    h("div", { style: { margin: "14px 0 10px" } }, trackChips()),
    quick,
    h("div", { style: { margin: "10px 0" } }, minutes),
    pyLine,
    body,
    h("div.grid2", { style: { marginTop: "18px" } },
      h("button", { type: "button", onclick: () => nav("#modes") }, "🎯 Modes"),
      h("button", { type: "button", onclick: () => nav("#review") }, "🔁 Review", mistakes ? h("span.badge", mistakes) : null),
      h("button", { type: "button", onclick: () => nav("#stories") }, "📚 Stories"),
      h("button", { type: "button", onclick: () => nav("#settings") }, "⚙️ Settings")),
    coach.hasKey() ? null : h("p.small.muted.center", "Coach off — everything works offline. Add a Claude API key in Settings for spoken feedback & live role-play."));
}

// ------------------------------------------------------------------ session
let current = null;

export async function startQuick() {
  await content.loadItems();
  startSession(sessions.quickSession());
}

export function startSession(sess) {
  if (!sess.items.length) return toast("Nothing available here yet — finish earlier Comeback weeks or enable Skip gates in Settings.");
  current = { ...sess, idx: 0, results: [], xp: 0, started: Date.now(), requeued: new Set() };
  if (sess.minutes) current.endAt = Date.now() + sess.minutes * 60000;
  if (location.hash !== "#session") history.pushState(null, "", "#session");
  renderItem();
}

function renderItem() {
  const c = current;
  if (!c) return home();
  const item = c.items[c.idx];
  const next = h("button.primary", { type: "button", disabled: true }, c.idx + 1 < c.items.length ? "Next →" : "Finish");
  const skip = h("button.ghost", { type: "button" }, "Skip");
  let answered = false;
  const ctx = {
    quick: c.quick, mock: c.mock,
    finish(result) {
      if (answered) return;
      answered = true;
      const xp = progress.record(item, result);
      c.xp += xp;
      c.results.push({ id: item.id, ...result });
      if (item.type === "flashcard" && result.rating === 1 && !c.requeued.has(item.id)) { c.requeued.add(item.id); c.items.push(item); }
      next.disabled = false;
      skip.classList.add("hidden");
      toast(`${result.correct ? "✓" : "✗"}  +${xp} XP`, 1400);
    },
  };
  const timer = h("span.timer");
  if (c.endAt) {
    const iv = setInterval(() => {
      if (!timer.isConnected) return clearInterval(iv);
      const left = (c.endAt - Date.now()) / 1000;
      timer.textContent = left > 0 ? fmtTime(left) : "0:00";
      timer.classList.toggle("low", left < 60);
    }, 500);
  }
  next.onclick = () => { stopSpeaking(); c.idx++; c.idx < c.items.length ? renderItem() : summary(); };
  skip.onclick = () => { stopSpeaking(); c.idx++; c.idx < c.items.length ? renderItem() : summary(); };
  const meta = h("div.row.wrap.small.muted", { style: { marginBottom: "6px" } },
    h("span.pill", content.TYPE_LABEL[item.type]), h("span.pill", content.stageTitle(item.pack, item.stage)),
    h("span.pill", "●".repeat(item.difficulty) + "○".repeat(3 - item.difficulty)));
  mount(
    h("div.topbar",
      h("button.ghost.icon-btn", { type: "button", "aria-label": "End session", onclick: () => { stopSpeaking(); c.results.length ? summary() : (current = null, nav("#home"), home()); } }, "✕"),
      h("div.progress", { "aria-label": `Item ${c.idx + 1} of ${c.items.length}` }, h("i", { style: { width: `${(100 * c.idx) / c.items.length}%` } })),
      timer.textContent || c.endAt ? timer : h("span.small.muted", `${c.idx + 1}/${c.items.length}`)),
    meta,
    h("section", { "data-item": item.id }, PLAYERS[item.type](item, ctx)),
    h("div.sticky-actions", skip, next));
}

function summary() {
  const c = current;
  current = null;
  const n = c.results.length, ok = c.results.filter(r => r.correct).length;
  const s = S();
  let extra = null;
  if (c.kind === "placement") {
    if (n && ok / n >= 0.8) { progress.unlockThrough(c.week); extra = h("div.feedback.good", `Placement passed (${ok}/${n}) — Week ${c.week + 1} unlocked.`); }
    else extra = h("div.feedback.info", `Placement: ${ok}/${n}. You need 80 % to test out — keep practising Week ${c.week}.`);
  }
  if (s.comeback.justUnlocked) {
    extra = h("div.feedback.good", s.comeback.justUnlocked > 4 ? "🎉 Comeback complete — progressive challenges are open." : `🎉 Week ${s.comeback.justUnlocked} unlocked!`);
    delete s.comeback.justUnlocked;
    store.save();
  }
  const missed = c.results.filter(r => !r.correct).map(r => content.getItem(r.id)).filter(Boolean);
  history.replaceState(null, "", "#home");
  mount(
    h("div.center", { style: { marginTop: "24px" } },
      h("div.kicker", c.title),
      h("div.huge", `+${c.xp} XP`),
      h("p", `${ok}/${n} correct · 🔥 ${progress.streakAlive()} day streak · ${Math.round((Date.now() - c.started) / 60000)} min`)),
    extra,
    missed.length ? h("div.card", h("b", "Coming back for review"), h("ul", missed.map(m => h("li", m.title || m.question || m.front || m.id)))) : null,
    h("div.stack", { style: { marginTop: "16px" } },
      h("button.primary.block", { type: "button", onclick: () => startSession(sessions.quickSession()) }, `Another ${S().profile.minutes} min`),
      h("button.block", { type: "button", onclick: () => home() }, "Home")));
}

// ------------------------------------------------------------------ modes
export function modes() {
  const s = S();
  const job = content.getPack(s.profile.track === "comeback" ? s.profile.jobPack : s.profile.track);
  const types = ["code", "challenge", "bug", "predict", "parsons", "flashcard", "design", "roleplay", "behavioral"];
  const pool = sessions.trackPool();
  const all = [...(content.getPack("comeback")?.items || []), ...(job?.items || [])];
  mount(
    back(),
    h("h1", "Practice modes"),
    h("p.small.muted", `Track: ${s.profile.track === "comeback" ? "Comeback" : job.manifest.title}`),
    h("h2", "By item type"),
    types.map(t => {
      const n = pool.filter(i => i.type === t).length;
      const total = all.filter(i => i.type === t).length;
      if (!total) return null;
      const gate = progress.TYPE_GATE[t];
      return h(`button.list-btn${n ? "" : ".lock"}`, { type: "button", onclick: () => startSession(sessions.typeSession(t)) },
        h("span", content.TYPE_LABEL[t]),
        h("span.small.muted", n ? `${n} items` : gate ? `🔒 after Comeback week ${gate - 1}` : "switch track"));
    }),
    job ? [
      h("h2", `By stage · ${job.manifest.title}`),
      job.manifest.stages.map(st => h("button.list-btn", { type: "button", onclick: () => startSession(sessions.stageSession(job.id, st.id)) },
        h("span", st.title), h("span.small.muted", `${job.items.filter(i => i.stage === st.id && progress.isUnlocked(i)).length} items`))),
      h("h2", "Full mock round (timed)"),
      h("p.small.muted", "One stage end to end against the clock — as close to the real round as the app can get."),
      job.manifest.stages.map(st => h("details.card",
        h("summary", `${st.title} · ${st.mockMinutes || 10} min`),
        h("p.small", h("b", "Tests: "), st.tests), h("p.small", h("b", "Method: "), st.methodology),
        h("button.primary.block", { type: "button", onclick: () => startSession(sessions.mockSession(job.id, st.id)) }, "Start mock"))),
    ] : null,
    h("h2", "Placement quizzes"),
    h("div.row.wrap", [1, 2, 3, 4].map(w => h("button", { type: "button", onclick: () => startSession(sessions.placementSession(w)) }, `Test out of week ${w}`))));
}

// ------------------------------------------------------------------ review
export function review() {
  const groups = progress.mistakesByPattern();
  const due = sessions.quickPreview().due;
  mount(
    back(),
    h("h1", "Review"),
    h("button.primary.block", { type: "button", disabled: !due, onclick: () => startSession(sessions.dueSession()) }, due ? `Review ${due} due items` : "Nothing due today"),
    h("h2", "This week's mistakes, by pattern"),
    groups.length ? groups.map(g => {
      const lesson = g.items.map(i => i.lesson || i.explanation || i.steps?.[0]?.lesson).find(Boolean);
      return h("div.card",
        h("div.row.spread", h("b", g.pattern), h("span.pill", `${g.misses} miss${g.misses > 1 ? "es" : ""}`)),
        lesson ? h("div.lesson", md(lesson)) : null,
        h("p.small.muted", g.items.map(i => i.title || i.question || i.front).slice(0, 3).join(" · ")),
        h("button.block", { type: "button", onclick: () => startSession(sessions.drillSession(g.ids, g.pattern)) }, `Drill these (${g.ids.length})`));
    }) : h("p.muted", "No open mistakes this week. Nice."));
}

// ------------------------------------------------------------------ stories
export function stories(editId) {
  const s = S();
  if (editId !== undefined) return storyEditor(editId);
  mount(
    back(),
    h("h1", "Story bank"),
    h("p.small.muted", "Your STAR stories, stored only on this device. Behavioral questions suggest which one fits."),
    h("button.primary.block", { type: "button", onclick: () => storyEditor(null) }, "+ New story"),
    s.stories.length ? s.stories.map(st => h("button.list-btn", { type: "button", onclick: () => storyEditor(st.id), style: { display: "block" } },
      h("b", st.title || "(untitled)"), h("div.small.muted", (st.tags || []).join(", ") || st.situation?.slice(0, 80) || ""))) :
      h("div.card", h("b", "Ideas to start"), h("ul",
        ["Built the company's AI platform solo: why, how, adoption", "A customer escalation on laser/AM equipment you turned around",
          "Saying no (or 'not yet') to a customer for safety/quality", "A mistake in production and how you fixed it",
          "Getting a skeptical team to adopt a new tool", "Working across Switzerland / China / US"].map(x => h("li", x)))));
}

function storyEditor(id) {
  const s = S();
  const st = s.stories.find(x => x.id === id) || { id: `st-${Date.now()}`, title: "", situation: "", task: "", action: "", result: "", reflection: "", tags: [] };
  const fields = [["title", "Title"], ["situation", "Situation"], ["task", "Task"], ["action", "Action — what *you* did"], ["result", "Result — numbers if you have them"], ["reflection", "Reflection — what you learned"]];
  const inputs = {};
  const tags = h("input", { type: "text", value: (st.tags || []).join(", "), placeholder: "tags: customer, safety, leadership" });
  mount(
    back("‹ Stories", "#stories"),
    h("h1", id ? "Edit story" : "New story"),
    h("p.small.muted", "Keep it generic — no confidential employer details."),
    fields.map(([k, label]) => {
      const el = k === "title" ? h("input", { type: "text", value: st[k] }) : h("textarea.answer", { style: { minHeight: "90px" } });
      if (k !== "title") el.value = st[k];
      inputs[k] = el;
      return h("label.stack", { style: { display: "block", marginTop: "12px" } }, h("b", label), k === "title" ? null : voiceInput(el, `story:${st.id}:${k}`), el);
    }),
    h("label", { style: { display: "block", marginTop: "12px" } }, h("b", "Tags"), tags),
    h("div.row", { style: { marginTop: "16px" } },
      h("button.primary.grow", {
        type: "button", onclick: () => {
          fields.forEach(([k]) => { st[k] = inputs[k].value.trim(); });
          st.tags = tags.value.split(",").map(t => t.trim()).filter(Boolean);
          st.updated = Date.now();
          if (!s.stories.includes(st)) s.stories.push(st);
          store.save(); toast("Story saved"); nav("#stories"); stories();
        },
      }, "Save"),
      id ? h("button", { type: "button", onclick: () => { if (confirm("Delete this story?")) { s.stories = s.stories.filter(x => x.id !== id); store.save(); stories(); } } }, "Delete") : null));
}

// ------------------------------------------------------------------ settings
export function settings() {
  const s = S();
  const p = s.profile;
  const key = h("input", { type: "password", value: store.getApiKey(), placeholder: "sk-ant-…", autocomplete: "off", "aria-label": "Claude API key" });
  const keyMsg = h("p.small");
  const toggle = (k, label, note) => {
    const cb = h("input", { type: "checkbox", checked: !!p[k], onchange: () => { p[k] = cb.checked; store.save(); } });
    return h("label.row", { style: { minHeight: "48px", borderBottom: "1px solid var(--border)" } }, h("span.grow", label, note ? h("div.small.muted", note) : null), cb);
  };
  const select = (k, opts, onchange) => {
    const el = h("select", { onchange: () => { p[k] = el.value; store.save(); onchange && onchange(); } }, opts.map(([v, l]) => h("option", { value: v, selected: p[k] === v }, l)));
    return el;
  };
  const fileIn = h("input", { type: "file", accept: "application/json,.json", class: "hidden" });
  fileIn.onchange = async () => {
    const f = fileIn.files[0];
    if (!f) return;
    try { store.importJSON(await f.text()); toast("Progress imported"); home(); nav("#home"); }
    catch (e) { toast("Import failed: " + e.message); }
  };
  mount(
    back(),
    h("h1", "Settings"),
    h("h2", "AI coach (optional)"),
    h("p.small.muted", "Your key is stored only on this device and sent only to api.anthropic.com. It is never included in exports. Everything works without it."),
    key,
    h("div.row.wrap", { style: { marginTop: "8px" } },
      h("button.primary", { type: "button", onclick: () => { store.setApiKey(key.value); keyMsg.textContent = key.value ? "Saved on this device." : "Key removed."; } }, "Save key"),
      h("button", {
        type: "button", onclick: async () => {
          store.setApiKey(key.value);
          keyMsg.textContent = "Testing…";
          try { const r = await coach.ask({ system: "Reply with exactly: ok", messages: [{ role: "user", content: "ping" }], maxTokens: 5 }); keyMsg.textContent = `Key works (${r}).`; }
          catch (e) { keyMsg.textContent = "Failed: " + e.message; }
        },
      }, "Test"),
      h("button.ghost", { type: "button", onclick: () => { store.setApiKey(""); key.value = ""; keyMsg.textContent = "Key removed."; } }, "Remove")),
    keyMsg,
    h("label", h("b", "Model"), select("model", coach.MODELS.map(m => [m.id, m.label]))),
    h("h2", "Practice"),
    toggle("timer", "Countdown on coding steps"),
    toggle("talkAloud", "Talk-out-loud reminders while coding"),
    toggle("voice", "Read feedback aloud", "Uses the phone's built-in voice; works offline"),
    toggle("skipGates", "Skip gates", "Open every item regardless of Comeback progress"),
    h("label", { style: { display: "block", marginTop: "12px" } }, h("b", "Theme"), select("theme", [["auto", "Match system"], ["light", "Light"], ["dark", "Dark"]], applyTheme)),
    h("h2", "Your data"),
    h("p.small.muted", `${s.attempts.length} attempts · ${Object.keys(s.srs).length} items in review · ${s.stories.length} stories`),
    h("div.grid2",
      h("button", { type: "button", onclick: () => download(`interview-trainer-${progress.today()}.json`, store.exportJSON()) }, "⬇ Export"),
      h("button", { type: "button", onclick: () => fileIn.click() }, "⬆ Import")),
    fileIn,
    h("button.ghost.block", { type: "button", style: { marginTop: "8px", color: "var(--bad)" }, onclick: () => { if (confirm("Erase all progress on this device?")) { store.resetAll(); home(); nav("#home"); } } }, "Reset progress"),
    h("h2", "About"),
    h("p.small.muted", `Content: ${content.allPacks().map(p => `${p.manifest.title} v${p.manifest.version} (${p.own.length})`).join(" · ")}`),
    h("p.small.muted", `Python: ${py.isReady() ? py.pyVersion() : py.status()} · App ${window.APP_VERSION || ""}`));
}

export function applyTheme() {
  const t = S().profile.theme;
  if (t === "auto") document.documentElement.removeAttribute("data-theme");
  else document.documentElement.setAttribute("data-theme", t);
}

export function route() {
  const hash = location.hash || "#home";
  if (hash.startsWith("#try/")) {   // deep link to one item: #try/<item-id>
    return content.loadItems().then(() => {
      const it = content.getItem(decodeURIComponent(hash.slice(5)));
      history.replaceState(null, "", "#home");
      it ? startSession({ kind: "drill", title: "Try", items: [it] }) : home();
    });
  }
  if (hash === "#session") return current ? renderItem() : (history.replaceState(null, "", "#home"), home());
  current = null;
  stopSpeaking();
  ({ "#modes": modes, "#review": review, "#stories": () => stories(), "#settings": settings }[hash] || home)();
}
