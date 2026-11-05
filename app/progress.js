// XP, levels, streaks, SM-2 spaced repetition, readiness and Comeback gates.
import * as store from "./store.js";
import { getPack, getItem } from "./content.js";

export const today = (d = new Date()) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
const addDays = (day, n) => { const d = new Date(day + "T12:00:00"); d.setDate(d.getDate() + n); return today(d); };
const daysBetween = (a, b) => Math.round((new Date(b + "T12:00:00") - new Date(a + "T12:00:00")) / 864e5);

// ---- Levels: level n needs 50·n·(n−1) XP in total (0, 100, 300, 600, …)
export function levelInfo(xp) {
  const level = Math.floor((1 + Math.sqrt(1 + (8 * xp) / 100)) / 2);
  const base = 50 * level * (level - 1), next = 50 * (level + 1) * level;
  return { level, into: xp - base, span: next - base };
}

// ---- XP for one attempt: difficulty × score, speed bonus, hint penalty
export function xpFor(item, { score, ms, hints = 0 }) {
  const base = { 1: 10, 2: 20, 3: 35 }[item.difficulty] || 10;
  const targetMs = (item.type === "predict" ? 20 : item.type === "flashcard" ? 15 : 60 * (item.minutes || 2)) * 1000;
  const speed = ms && ms < targetMs * 0.6 ? 1.25 : 1;
  return Math.max(2, Math.round(base * score * speed * Math.max(0.4, 1 - 0.2 * hints)));
}

// ---- SM-2. quality 0–5; < 3 means "missed" and the item comes back tomorrow.
export function sm2(prev, quality, day = today()) {
  const c = prev ? { ...prev } : { ef: 2.5, interval: 0, reps: 0, lapses: 0 };
  if (quality < 3) {
    c.reps = 0; c.interval = 1; c.lapses = (c.lapses || 0) + 1;
  } else {
    c.reps += 1;
    c.interval = c.reps === 1 ? 1 : c.reps === 2 ? 3 : Math.round(c.interval * c.ef);
  }
  c.ef = Math.max(1.3, c.ef + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02));
  c.due = addDays(day, c.interval);
  return c;
}

export function qualityFrom({ correct, score, hints = 0, rating }) {
  if (rating != null) return rating;           // flashcards: self-rated
  if (!correct) return score > 0.4 ? 2 : 1;
  if (hints >= 2 || score < 0.7) return 3;
  return hints ? 4 : 5;
}

// ---- Record an attempt: XP, streak, SRS, per-item memory
export function record(item, result) {
  const s = store.get();
  const day = today();
  const xp = xpFor(item, result);
  s.xp += xp;
  s.days[day] = s.days[day] || { xp: 0, items: 0 };
  s.days[day].xp += xp;
  s.days[day].items += 1;
  if (s.streak.lastDay !== day) {
    s.streak.count = s.streak.lastDay && daysBetween(s.streak.lastDay, day) === 1 ? s.streak.count + 1 : 1;
    s.streak.lastDay = day;
    s.streak.best = Math.max(s.streak.best, s.streak.count);
  }
  s.attempts.push({
    id: item.id, pack: item.pack, stage: item.stage, type: item.type, pattern: item.pattern || item.type,
    week: item.week, correct: !!result.correct, score: +(result.score ?? (result.correct ? 1 : 0)).toFixed(2),
    ms: result.ms || 0, hints: result.hints || 0, day, t: Date.now(),
  });
  s.srs[item.id] = sm2(s.srs[item.id], qualityFrom(result), day);
  const mem = s.items[item.id] = s.items[item.id] || { seen: 0 };
  mem.seen += 1;
  mem.last = !!result.correct;
  checkGate();
  store.save();
  return xp;
}

export function streakAlive() {
  const s = store.get();
  if (!s.streak.lastDay) return 0;
  const gap = daysBetween(s.streak.lastDay, today());
  return gap <= 1 ? s.streak.count : 0;
}

export const dueIds = () => {
  const d = today();
  return Object.entries(store.get().srs).filter(([, c]) => c.due <= d).map(([id]) => id);
};

// ---- Readiness per stage: recent accuracy × coverage (0–100)
export function readiness(packId) {
  const pack = getPack(packId);
  if (!pack) return [];
  const atts = store.get().attempts;
  const stageOf = id => pack.items.find(i => i.id === id)?.stage;
  return pack.manifest.stages.map(st => {
    const mine = atts.filter(a => (a.pack === packId ? a.stage : stageOf(a.id)) === st.id).slice(-20);
    if (!mine.length) return { ...st, value: 0, n: 0 };
    let wsum = 0, acc = 0;
    mine.forEach((a, i) => { const w = 1 + i / mine.length; wsum += w; acc += w * a.score; });
    const distinct = new Set(mine.map(a => a.id)).size;
    const coverage = Math.min(1, distinct / 8);
    return { ...st, value: Math.round(100 * (acc / wsum) * (0.4 + 0.6 * coverage)), n: mine.length };
  });
}

// ---- Comeback gate: week N passes when ≥ 80 % of its items were last answered correctly
export function weekStats(week) {
  const cb = getPack("comeback");
  const items = cb ? cb.items.filter(i => i.week === week) : [];
  const mem = store.get().items;
  const correct = items.filter(i => mem[i.id]?.last === true).length;
  const tried = items.filter(i => mem[i.id]?.seen).length;
  return { total: items.length, correct, tried, pct: items.length ? correct / items.length : 0 };
}

export function checkGate() {
  const s = store.get();
  while (s.comeback.week <= 4 && weekStats(s.comeback.week).total && weekStats(s.comeback.week).pct >= 0.8) {
    s.comeback.week += 1;
    s.comeback.justUnlocked = s.comeback.week;
  }
}

export function unlockThrough(week) {
  const s = store.get();
  s.comeback.week = Math.max(s.comeback.week, week + 1);
  store.save();
}

// Which job-pack item types are open, given Comeback progress (see docs/PLAN.md).
export const TYPE_GATE = { predict: 2, bug: 3, parsons: 3, challenge: 4 };
export function isUnlocked(item) {
  const s = store.get();
  if (s.profile.skipGates) return true;
  if (item.pack === "comeback") return item.week <= s.comeback.week;
  return s.comeback.week >= (TYPE_GATE[item.type] || 0);
}

// Mistakes in the last 7 days whose latest attempt is still wrong, grouped by pattern.
export function mistakesByPattern() {
  const s = store.get();
  const since = addDays(today(), -7);
  const latest = {};
  for (const a of s.attempts) latest[a.id] = a;
  const groups = {};
  for (const a of s.attempts) {
    if (a.day < since || a.correct || latest[a.id].correct) continue;
    const g = groups[a.pattern] = groups[a.pattern] || { pattern: a.pattern, ids: new Set(), misses: 0 };
    g.ids.add(a.id);
    g.misses += 1;
  }
  return Object.values(groups)
    .map(g => ({ ...g, ids: [...g.ids], items: [...g.ids].map(getItem).filter(Boolean) }))
    .sort((a, b) => b.misses - a.misses);
}
