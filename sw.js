// Service worker: precache everything (app shell, packs, Pyodide) on install,
// then serve cache-first so the app — including Python — works offline.
// tools/build.py rewrites the two lines below whenever any file changes.
const VERSION = "01a501d7fa";
const ASSETS = ["./index.html", "./manifest.webmanifest", "./app/coach.js", "./app/content.js", "./app/editor.js", "./app/harness.py", "./app/main.js", "./app/players.js", "./app/progress.js", "./app/py-worker.js", "./app/python.js", "./app/screens.js", "./app/session.js", "./app/store.js", "./app/styles.css", "./app/ui.js", "./app/voice.js", "./icons/apple-touch-icon.png", "./icons/icon-192.png", "./icons/icon-512.png", "./icons/icon.svg", "./packs/index.json", "./packs/comeback/pack.json", "./packs/comeback/week1.json", "./packs/comeback/week2.json", "./packs/comeback/week3.json", "./packs/comeback/week4.json", "./packs/anthropic-fde/pack.json", "./packs/anthropic-fde/challenges-a.json", "./packs/anthropic-fde/challenges-b.json", "./packs/anthropic-fde/bugs.json", "./packs/anthropic-fde/predict.json", "./packs/anthropic-fde/parsons.json", "./packs/anthropic-fde/flashcards.json", "./packs/anthropic-fde/design.json", "./packs/anthropic-fde/roleplay.json", "./packs/anthropic-fde/behavioral.json", "./packs/anthropic-applied-ai-architect/pack.json", "./packs/anthropic-applied-ai-architect/design.json", "./packs/anthropic-applied-ai-architect/roleplay.json", "./packs/anthropic-applied-ai-architect/behavioral.json", "./packs/anthropic-applied-ai-architect/flashcards.json", "./vendor/pyodide/pyodide.mjs", "./vendor/pyodide/pyodide.asm.mjs", "./vendor/pyodide/pyodide.asm.wasm", "./vendor/pyodide/python_stdlib.zip", "./vendor/pyodide/pyodide-lock.json"];

const CACHE = `it-${VERSION}`;

self.addEventListener("install", event => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    // Reuse unchanged big files (Pyodide) from the previous cache instead of re-downloading.
    const old = (await caches.keys()).filter(k => k !== CACHE && k.startsWith("it-"));
    for (const url of ASSETS) {
      let hit = null;
      for (const k of old) { hit = await (await caches.open(k)).match(url); if (hit && url.includes("vendor/")) break; hit = null; }
      if (hit) await cache.put(url, hit);
      else await cache.add(new Request(url, { cache: "reload" }));
    }
    await self.skipWaiting();
  })());
});

self.addEventListener("activate", event => {
  event.waitUntil((async () => {
    for (const k of await caches.keys()) if (k !== CACHE) await caches.delete(k);
    await self.clients.claim();
  })());
});

self.addEventListener("fetch", event => {
  const req = event.request;
  const url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== location.origin) return; // e.g. api.anthropic.com: never cached
  event.respondWith((async () => {
    const cache = await caches.open(CACHE);
    const hit = await cache.match(req, { ignoreSearch: true }) ||
      (req.mode === "navigate" ? await cache.match("./index.html") : null);
    if (hit) return hit;
    try {
      const res = await fetch(req);
      if (res.ok) cache.put(req, res.clone());
      return res;
    } catch (e) {
      return new Response("Offline", { status: 503 });
    }
  })());
});
