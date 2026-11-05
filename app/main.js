// Entry point: load state + pack manifests, render Home, then warm up
// Python and the service worker in the background.
import * as store from "./store.js";
import * as content from "./content.js";
import * as py from "./python.js";
import { route, applyTheme } from "./screens.js";
import { checkGate } from "./progress.js";

window.APP_VERSION = "1.0.0";

async function boot() {
  store.load();
  applyTheme();
  await content.loadManifests();
  route();                         // Home renders from the small manifests…
  content.loadItems().then(() => { // …item files stream in behind it
    checkGate();
    if ((location.hash || "#home") === "#home") route();
  });
  window.addEventListener("hashchange", route);
  window.addEventListener("popstate", () => { if (location.hash === "#session") route(); });
  // Pyodide loads after the first paint so Home is instant.
  setTimeout(() => py.start(), 300);
  if ("serviceWorker" in navigator && location.protocol !== "file:") {
    navigator.serviceWorker.register("sw.js").catch(e => console.warn("SW", e));
  }
  document.documentElement.dataset.ready = "1";
}

boot().catch(e => {
  console.error(e);
  document.getElementById("app").innerHTML = `<p style="padding:20px">Couldn't start: ${String(e.message || e)}. Check your connection and reload.</p>`;
});
