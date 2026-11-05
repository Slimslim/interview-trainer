// Main-thread side of the Python runner. Starts the worker lazily, queues
// requests, and kills + restarts the worker if code runs too long.
let worker = null, ready = false, version = "", seq = 0;
const pending = new Map();
const listeners = new Set();
const TIMEOUT_MS = 8000;

function setStatus(s) { listeners.forEach(fn => fn(s)); }
export const onStatus = fn => { listeners.add(fn); fn(status()); return () => listeners.delete(fn); };
export const status = () => (ready ? "ready" : worker ? "loading" : "idle");
export const isReady = () => ready;
export const pyVersion = () => version;

export function start() {
  if (worker) return;
  worker = new Worker(new URL("./py-worker.js", import.meta.url), { type: "module" });
  setStatus("loading");
  worker.onmessage = ({ data }) => {
    if (data.ready) { ready = true; version = data.version; setStatus("ready"); return; }
    if (data.fatal) { console.error(data.fatal); setStatus("error"); return; }
    const p = pending.get(data.id);
    if (p) { clearTimeout(p.timer); pending.delete(data.id); p.resolve(data.result); }
  };
  worker.onerror = e => { console.error(e); setStatus("error"); };
}

function restart() {
  worker?.terminate();
  worker = null; ready = false;
  for (const [, p] of pending) { clearTimeout(p.timer); p.resolve(p.timeoutResult); }
  pending.clear();
  start();
}

function call(msg) {
  start();
  return new Promise(resolve => {
    const id = ++seq;
    const timeoutResult = { ok: false, tests: [], stdout: "", error: `Stopped after ${TIMEOUT_MS / 1000}s — is there an infinite loop?` };
    // The timeout only starts once Python is ready, so a slow first load isn't counted.
    const arm = () => setTimeout(() => { pending.delete(id); resolve(timeoutResult); restart(); }, TIMEOUT_MS);
    const entry = { resolve, timeoutResult, timer: null };
    pending.set(id, entry);
    const send = () => { entry.timer = arm(); worker.postMessage({ id, ...msg }); };
    if (ready) send();
    else {
      const off = onStatus(s => { if (s === "ready") { off(); send(); } });
    }
  });
}

export const runTests = (code, tests) => call({ cmd: "run_tests", code, tests });
export const runCode = code => call({ cmd: "run_code", code });
