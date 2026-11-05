// Builds sessions: Quick start, by stage, by type, full mock round,
// placement quiz, and review drills.
import * as store from "./store.js";
import { getPack, getItem, itemMinutes } from "./content.js";
import { dueIds, readiness, isUnlocked, weekStats } from "./progress.js";
import { shuffle } from "./ui.js";

const LONG = new Set(["challenge", "design", "roleplay"]);

export function trackPool() {
  const s = store.get();
  if (s.profile.track === "comeback") {
    const cb = getPack("comeback")?.items || [];
    const job = getPack(s.profile.jobPack)?.items || [];
    // Non-coding interview prep starts on day one, alongside the Comeback reps.
    return [...cb, ...job.filter(i => i.type === "flashcard" || i.type === "behavioral")].filter(isUnlocked);
  }
  return (getPack(s.profile.track)?.items || []).filter(isUnlocked);
}

// Order: unseen first, then least recently / least successfully seen.
function freshness(items) {
  const mem = store.get().items;
  return shuffle(items).sort((a, b) => {
    const ma = mem[a.id], mb = mem[b.id];
    const ka = !ma ? 0 : ma.last ? 2 : 1, kb = !mb ? 0 : mb.last ? 2 : 1;
    return ka - kb;
  });
}

// Fill `minutes` from candidate lists in priority order, mixing item types.
function fill(minutes, lists, { allowLong = minutes >= 8 } = {}) {
  const chosen = [], ids = new Set();
  let t = 0;
  for (const { items, share } of lists) {
    const cap = minutes * share;
    let used = 0;
    for (const it of items) {
      if (ids.has(it.id)) continue;
      const m = itemMinutes(it);
      if (LONG.has(it.type) && !allowLong) continue;
      if (t + m > minutes + 0.5 || used + m > cap + 0.5) continue;
      const last2 = chosen.slice(-2).map(c => c.type);
      if (last2.length === 2 && last2.every(x => x === it.type) && items.length > 6) continue;
      chosen.push(it); ids.add(it.id); t += m; used += m;
      if (t >= minutes) break;
    }
  }
  return chosen;
}

export function quickSession() {
  const s = store.get();
  const minutes = s.profile.minutes || 5;
  const pool = trackPool();
  const due = new Set(dueIds());
  const dueItems = shuffle(pool.filter(i => due.has(i.id)));
  let focus, focusLabel, handsOn;
  const HANDS_ON = new Set(["code", "challenge", "bug", "parsons"]);
  if (s.profile.track === "comeback") {
    const week = Math.min(4, s.comeback.week);
    focus = freshness(pool.filter(i => i.week === week && !store.get().items[i.id]?.last));
    handsOn = focus.filter(i => HANDS_ON.has(i.type));
    focusLabel = `Week ${week}`;
  } else {
    const r = readiness(s.profile.track).sort((a, b) => a.value - b.value);
    const weak = r.find(st => pool.some(i => i.stage === st.id)) || r[0];
    focus = freshness(pool.filter(i => i.stage === weak?.id));
    focusLabel = weak?.title || "";
    // Every job-track session includes real coding: a challenge level when there's
    // time, otherwise a bug fix or Parsons puzzle.
    const coding = freshness(pool.filter(i => HANDS_ON.has(i.type) && i.type !== "code"));
    handsOn = minutes >= 8 ? [...coding.filter(i => i.type === "challenge"), ...coding] : coding.filter(i => i.type !== "challenge");
  }
  const comeback = s.profile.track === "comeback";
  const rest = freshness(pool.filter(i => !comeback || i.pack === "comeback"));
  const extras = comeback ? freshness(pool.filter(i => i.pack !== "comeback")) : [];
  let items = fill(minutes, [{ items: handsOn, share: 0.7 }, { items: dueItems, share: 0.4 },
    { items: focus, share: 0.5 }, { items: extras, share: 0.15 }, { items: rest, share: 1 }], { allowLong: minutes >= 8 });
  // A 5-minute job-track session still gets one challenge level when coding is the focus.
  if (!items.length) items = rest.slice(0, 3);
  return { kind: "quick", title: `Quick ${minutes}-min`, items: comeback ? codeFirst(items) : shuffleMild(items), focusLabel, quick: true };
}

// Comeback: open with a hands-on code rep, interleave the rest.
function codeFirst(items) {
  const code = items.filter(i => i.type === "code"), other = items.filter(i => i.type !== "code");
  const out = [];
  while (code.length || other.length) { if (code.length) out.push(code.shift()); if (other.length) out.push(other.shift()); }
  return out;
}

// Job tracks: keep reflex items first so the session starts fast.
function shuffleMild(items) {
  const order = { flashcard: 0, predict: 0, code: 1, parsons: 1, bug: 1, behavioral: 2, challenge: 3, design: 3, roleplay: 3 };
  return items.map((it, i) => ({ it, k: order[it.type] + (i % 3) * 0.3 })).sort((a, b) => a.k - b.k).map(x => x.it);
}

export function quickPreview() {
  const s = store.get();
  const pool = trackPool();
  const due = new Set(dueIds());
  return { due: pool.filter(i => due.has(i.id)).length, pool: pool.length };
}

export function stageSession(packId, stageId) {
  const pack = getPack(packId);
  const items = freshness(pack.items.filter(i => i.stage === stageId && isUnlocked(i)));
  return { kind: "stage", title: pack.manifest.stages.find(s => s.id === stageId)?.title, items: fill(10, [{ items, share: 1 }], { allowLong: true }) };
}

export function typeSession(type) {
  const items = freshness(trackPool().filter(i => i.type === type));
  const minutes = Math.max(store.get().profile.minutes, LONG.has(type) ? 10 : 5);
  return { kind: "type", title: type, items: fill(minutes, [{ items, share: 1 }], { allowLong: true }) };
}

export function mockSession(packId, stageId) {
  const pack = getPack(packId);
  const st = pack.manifest.stages.find(s => s.id === stageId);
  const minutes = st.mockMinutes || 10;
  const stageItems = pack.items.filter(i => i.stage === stageId);
  const pick = type => freshness(stageItems.filter(i => i.type === type));
  let items;
  if (pick("challenge").length) items = pick("challenge").slice(0, 1);
  else if (pick("design").length && stageId !== "customer") items = pick("design").slice(0, 1);
  else if (pick("roleplay").length) items = [...pick("roleplay").slice(0, 1), ...pick("behavioral").slice(0, 1)];
  else items = fill(minutes, [{ items: pick("behavioral"), share: 0.8 }, { items: freshness(stageItems), share: 1 }]);
  return { kind: "mock", title: `Mock · ${st.title}`, items, minutes, mock: true };
}

export function placementSession(week) {
  const items = shuffle(getPack("comeback").items.filter(i => i.week === week && (i.type === "predict" || i.type === "code"))).slice(0, 10);
  return { kind: "placement", week, title: `Placement · Week ${week}`, items };
}

export function drillSession(ids, title = "Review") {
  return { kind: "drill", title, items: ids.map(getItem).filter(Boolean) };
}

export function dueSession() {
  const due = new Set(dueIds());
  return { kind: "due", title: "Due for review", items: fill(10, [{ items: shuffle(trackPool().filter(i => due.has(i.id))), share: 1 }], { allowLong: true }) };
}

export { weekStats };
