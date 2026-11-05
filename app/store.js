// Local persistence. Everything is wrapped in try/catch: private mode or a
// full disk must never break the app — we just keep state in memory.
const KEY = "it.v1";
const KEY_API = "it.apikey";

export const DEFAULT_STATE = () => ({
  version: 1,
  profile: {
    track: "comeback", jobPack: "anthropic-fde", theme: "auto", timer: true, talkAloud: true,
    voice: true, minutes: 5, skipGates: false, model: "claude-sonnet-5-5",
  },
  xp: 0,
  streak: { count: 0, best: 0, lastDay: null },
  days: {},
  attempts: [],
  srs: {},
  items: {},
  comeback: { week: 1 },
  stories: [],
  answers: {},
});

let state = null;

function merge(base, saved) {
  for (const [k, v] of Object.entries(saved || {})) {
    if (v && typeof v === "object" && !Array.isArray(v) && base[k] && typeof base[k] === "object" && !Array.isArray(base[k])) {
      merge(base[k], v);
    } else base[k] = v;
  }
  return base;
}

export function load() {
  let saved = null;
  try { saved = JSON.parse(localStorage.getItem(KEY) || "null"); } catch { saved = null; }
  state = merge(DEFAULT_STATE(), saved);
  return state;
}

export function get() { return state || load(); }

export function save() {
  try {
    const s = get();
    if (s.attempts.length > 3000) s.attempts = s.attempts.slice(-3000);
    localStorage.setItem(KEY, JSON.stringify(s));
    return true;
  } catch (e) {
    console.warn("save failed", e);
    return false;
  }
}

export function exportJSON() {
  return JSON.stringify({ app: "interview-trainer", exported: new Date().toISOString(), state: get() }, null, 1);
}

export function importJSON(text) {
  const doc = JSON.parse(text);
  const incoming = doc && doc.app === "interview-trainer" ? doc.state : null;
  if (!incoming || typeof incoming !== "object" || !Array.isArray(incoming.attempts)) {
    throw new Error("Not an Interview Trainer export file");
  }
  state = merge(DEFAULT_STATE(), incoming);
  save();
  return state;
}

export function resetAll() {
  state = DEFAULT_STATE();
  save();
}

export function getApiKey() {
  try { return localStorage.getItem(KEY_API) || ""; } catch { return ""; }
}
export function setApiKey(k) {
  try { k ? localStorage.setItem(KEY_API, k.trim()) : localStorage.removeItem(KEY_API); } catch { /* ignore */ }
}

// ---- Audio recordings in IndexedDB (device only, never exported) ----
const DB = "it-audio";
function db() {
  return new Promise((resolve, reject) => {
    try {
      const req = indexedDB.open(DB, 1);
      req.onupgradeneeded = () => req.result.createObjectStore("rec", { keyPath: "id" });
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    } catch (e) { reject(e); }
  });
}
export async function saveRecording(itemId, blob) {
  try {
    const d = await db();
    const id = `${itemId}:${Date.now()}`;
    await new Promise((res, rej) => {
      const tx = d.transaction("rec", "readwrite");
      tx.objectStore("rec").put({ id, itemId, t: Date.now(), blob });
      tx.oncomplete = res; tx.onerror = () => rej(tx.error);
    });
    return id;
  } catch (e) { console.warn("recording not saved", e); return null; }
}
export async function listRecordings(itemId) {
  try {
    const d = await db();
    return await new Promise((res, rej) => {
      const req = d.transaction("rec").objectStore("rec").getAll();
      req.onsuccess = () => res(req.result.filter(r => r.itemId === itemId).sort((a, b) => b.t - a.t));
      req.onerror = () => rej(req.error);
    });
  } catch { return []; }
}
