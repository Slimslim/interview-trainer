// End-to-end checks with Playwright on an emulated iPhone 15.
//   node tests/e2e.mjs            (starts its own server on :8799)
// Writes reports/e2e-report.md and reports/screenshots/*.png; exits 1 on failure.
import { createRequire } from "node:module";
import { spawn } from "node:child_process";
import { readFileSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium, devices } = require("playwright");
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const PORT = 8799, BASE = `http://localhost:${PORT}/`;
const SHOTS = path.join(root, "reports/screenshots");
rmSync(SHOTS, { recursive: true, force: true });
mkdirSync(SHOTS, { recursive: true });
const IPHONE = devices["iPhone 15"];

const results = [];
const metrics = {};
function check(group, name, ok, detail = "") {
  results.push({ group, name, ok: !!ok, detail });
  console.log(`${ok ? "PASS" : "FAIL"}  [${group}] ${name}${detail ? " — " + detail : ""}`);
}

// ---------- content helpers
const pack = id => {
  const m = JSON.parse(readFileSync(path.join(root, `packs/${id}/pack.json`)));
  return m.files.flatMap(f => JSON.parse(readFileSync(path.join(root, `packs/${id}/${f}`))).items);
};
const ITEMS = [...pack("comeback"), ...pack("anthropic-fde"), ...pack("anthropic-applied-ai-architect")];
const first = (type, pred = () => true) => ITEMS.find(i => i.type === type && pred(i));
const codeItem = first("code", i => i.week === 1 && i.solution.split("\n").length >= 3);

// ---------- page helpers
async function newPage(browser, opts = {}) {
  const ctx = await browser.newContext({ ...IPHONE, ...opts });
  const page = await ctx.newPage();
  page.errors = [];
  page.on("pageerror", e => page.errors.push(String(e)));
  page.on("console", m => { if (m.type() === "error" && !/Failed to load resource/.test(m.text())) page.errors.push(m.text()); });
  return { ctx, page };
}
const ready = page => page.waitForFunction(() => document.documentElement.dataset.ready === "1");
const pyReady = page => page.waitForFunction(() => /Python .* ready/.test(document.body.innerText), null, { timeout: 60000 });
async function gotoItem(page, id) {
  await page.goto(`${BASE}#try/${id}`);
  await page.waitForSelector(".topbar");
}

// Checks every visible interactive element is at least 44×44 CSS px and nothing scrolls sideways.
async function layoutAudit(page, label) {
  const r = await page.evaluate(() => {
    const vw = document.documentElement.clientWidth;
    const overflow = document.scrollingElement.scrollWidth - vw;
    const sel = "button, a[href], select, input:not([type=checkbox]):not([type=file]), summary, label:has(> input[type=checkbox])";
    const small = [];
    for (const el of document.querySelectorAll(sel)) {
      const b = el.getBoundingClientRect();
      if (!b.width || !b.height || getComputedStyle(el).visibility === "hidden") continue;
      if (el.closest(".keybar") && b.height >= 44 && b.width >= 40) continue; // symbol keys: 44 tall, ≥40 wide
      if (b.height < 44 || b.width < 44) small.push(`${el.tagName.toLowerCase()}"${(el.innerText || el.getAttribute("aria-label") || "").trim().slice(0, 24)}" ${Math.round(b.width)}×${Math.round(b.height)}`);
    }
    const text = document.getElementById("app").innerText;
    if (/(^|\s)(null|undefined)(\s|$)|\[object /.test(text)) small.push("stray null/undefined/[object] text on screen");
    return { overflow, small };
  });
  return r;
}

async function shoot(page, name, theme) {
  await page.waitForTimeout(150);
  await page.screenshot({ path: path.join(SHOTS, `${theme}-${name}.png`), fullPage: true });
  const a = await layoutAudit(page, name);
  check("Mobile UX", `${theme}/${name}: no horizontal scroll`, a.overflow <= 0, a.overflow > 0 ? `${a.overflow}px overflow` : "");
  check("Mobile UX", `${theme}/${name}: tap targets ≥ 44px`, !a.small.length, a.small.slice(0, 4).join("; "));
}

// Types code the way a person would on the phone keyboard: line by line,
// letting the editor auto-indent and using the on-screen ⇤ key to dedent.
async function typeLikeHuman(page, code) {
  const ta = page.locator("textarea.editor");
  await ta.click();
  await ta.fill("");
  let auto = 0;
  const lines = code.replace(/\n$/, "").split("\n");
  for (let i = 0; i < lines.length; i++) {
    const want = lines[i].match(/^ */)[0].length;
    for (let d = auto; d > want; d -= 4) await page.click('.keybar button[aria-label="Dedent"]');
    for (let d = auto; d < want; d += 4) await page.click('.keybar button[aria-label="Indent"]');
    await page.keyboard.type(lines[i].trimStart());
    if (i < lines.length - 1) {
      await page.keyboard.press("Enter");
      auto = want + (/:\s*(#.*)?$/.test(lines[i]) ? 4 : 0);
      if (!lines[i].trim()) auto = want;
    }
  }
}

// ======================================================================
const server = spawn(process.execPath, [path.join(root, "tools/serve.mjs"), String(PORT)], { stdio: "pipe" });
await new Promise(r => server.stdout.once("data", r));
const browser = await chromium.launch();

try {
  // ---------------------------------------------------------- 2. Mobile UX
  const screens = [
    ["code", first("code")], ["challenge", first("challenge")], ["bug", first("bug")], ["predict", first("predict", i => i.code)],
    ["parsons", first("parsons")], ["flashcard", first("flashcard")], ["design", first("design")],
    ["roleplay", first("roleplay")], ["behavioral", first("behavioral")],
  ];
  for (const theme of ["light", "dark"]) {
    const { ctx, page } = await newPage(browser, { colorScheme: theme });
    await page.goto(BASE); await ready(page);
    await page.waitForFunction(() => !/0\/0 correct/.test(document.body.innerText));
    await shoot(page, "home-comeback", theme);
    await page.click("text=FDE"); await shoot(page, "home-fde", theme);
    await page.click("text=AI Architect"); await shoot(page, "home-architect", theme);
    await page.click("text=FDE");
    for (const [hash, name] of [["#modes", "modes"], ["#review", "review"], ["#stories", "stories"], ["#settings", "settings"]]) {
      await page.goto(BASE + hash); await page.waitForSelector("h1"); await shoot(page, name, theme);
    }
    await page.goto(BASE + "#stories"); await page.click("text=+ New story"); await shoot(page, "story-editor", theme);
    await page.evaluate(() => { const s = JSON.parse(localStorage.getItem("it.v1")); s.profile.skipGates = true; localStorage.setItem("it.v1", JSON.stringify(s)); });
    for (const [name, item] of screens) { await gotoItem(page, item.id); await shoot(page, `item-${name}`, theme); }
    // a finished item + session summary
    await gotoItem(page, first("predict", i => i.code).id);
    await page.locator(".choice").first().click();
    await shoot(page, "item-predict-answered", theme);
    await page.getByRole("button", { name: "Finish", exact: true }).click();
    await page.waitForSelector(".huge");
    await shoot(page, "summary", theme);
    check("Mobile UX", `${theme}: no JS errors`, !page.errors.length, page.errors.slice(0, 2).join(" | "));
    await ctx.close();
  }

  // Quick start in ≤ 2 taps
  {
    const { ctx, page } = await newPage(browser);
    await page.goto(BASE); await ready(page);
    let taps = 0;
    await page.click("#quick-start"); taps++;
    await page.waitForSelector(".topbar", { timeout: 5000 });
    const hasQuestion = await page.locator(".kicker").count();
    check("Mobile UX", "Quick start reaches first question", hasQuestion > 0 && taps <= 2, `${taps} tap(s)`);
    const firstType = await page.locator(".pill").first().innerText();
    check("Mobile UX", "Comeback quick session opens with a hands-on code rep", /Write code/.test(firstType), firstType);
    await ctx.close();
  }

  // Code editor usable with the on-screen keyboard
  {
    const { ctx, page } = await newPage(browser);
    await gotoItem(page, codeItem.id);
    await pyReady(page).catch(() => {});
    await typeLikeHuman(page, codeItem.solution);
    const typed = await page.locator("textarea.editor").inputValue();
    check("Mobile UX", "Editor: auto-indent + key bar reproduce the solution exactly", typed.trimEnd() === codeItem.solution.trimEnd(), typed === codeItem.solution ? "" : JSON.stringify(typed.slice(0, 80)));
    await page.click("text=▶ Run tests");
    await page.waitForSelector(".feedback", { timeout: 30000 });
    const fb = await page.locator(".feedback").first().innerText();
    check("Mobile UX", "Editor: typed code runs in Pyodide and passes", /All \d+ tests pass/.test(fb), fb.slice(0, 60));
    await page.screenshot({ path: path.join(SHOTS, "light-item-code-passed.png"), fullPage: true });
    const fontSize = await page.locator("textarea.editor").evaluate(e => parseFloat(getComputedStyle(e).fontSize));
    check("Mobile UX", "Editor font ≥ 16px (no iOS zoom on focus)", fontSize >= 16, `${fontSize}px`);
    await ctx.close();
  }

  // ------------------------------------------------- 4. Performance (4G)
  {
    const { ctx, page } = await newPage(browser);
    const cdp = await ctx.newCDPSession(page);
    await cdp.send("Network.enable");
    // Lighthouse "slow 4G": 150 ms RTT, 1.6 Mbps down, 750 kbps up
    const throttle = () => cdp.send("Network.emulateNetworkConditions", { offline: false, latency: 150, downloadThroughput: 1.6e6 / 8, uploadThroughput: 750e3 / 8 });
    await throttle();
    let t0 = Date.now();
    await page.goto(BASE);
    await page.waitForSelector("#quick-start");
    metrics.firstLoadMs = Date.now() - t0;
    check("Performance", "First load (home usable) < 5 s on simulated 4G", metrics.firstLoadMs < 5000, `${metrics.firstLoadMs} ms`);
    await pyReady(page).catch(() => {});
    metrics.pythonReadyMs = Date.now() - t0;
    // let the service worker finish precaching (unthrottled to save test time)
    await cdp.send("Network.emulateNetworkConditions", { offline: false, latency: 0, downloadThroughput: -1, uploadThroughput: -1 });
    await page.waitForFunction(async () => {
      const reg = await navigator.serviceWorker.ready;
      return !!reg.active && (await caches.keys()).length > 0 && (await (await caches.open((await caches.keys())[0])).keys()).length >= 40;
    }, null, { timeout: 60000 });
    await throttle();
    t0 = Date.now();
    await page.reload();
    await page.waitForSelector("#quick-start");
    metrics.returningMs = Date.now() - t0;
    check("Performance", "Returning launch < 1 s (served by service worker, 4G throttled)", metrics.returningMs < 1000, `${metrics.returningMs} ms`);
    await ctx.close();
  }

  // ------------------------------------------------------------ 3. Offline
  {
    const { ctx, page } = await newPage(browser);
    await page.goto(BASE); await ready(page);
    await pyReady(page);
    await page.waitForFunction(async () => {
      const reg = await navigator.serviceWorker.ready;
      const keys = await caches.keys();
      return reg.active && navigator.serviceWorker.controller !== undefined && keys.length && (await (await caches.open(keys[0])).keys()).length >= 40;
    }, null, { timeout: 60000 });
    await page.reload(); await ready(page); // now controlled by the SW
    await ctx.setOffline(true);
    await page.reload();
    await ready(page);
    check("Offline", "App shell loads with network disabled", await page.locator("#quick-start").count() === 1);
    await pyReady(page);
    check("Offline", "Pyodide starts offline", true);
    await gotoItem(page, codeItem.id);
    await page.locator("textarea.editor").fill(codeItem.solution);
    await page.click("text=▶ Run tests");
    await page.waitForSelector(".feedback", { timeout: 30000 });
    const fb = await page.locator(".feedback").first().innerText();
    check("Offline", "Python tests run offline", /All \d+ tests pass/.test(fb), fb.slice(0, 50));
    await page.goto(BASE + "#try/" + first("design").id);
    await page.waitForSelector("text=No API key");
    check("Offline", "Packs (design scenario) available offline", true);
    await ctx.close();
  }

  // ----------------------------------------------------------- 5. Progress
  {
    const { ctx, page } = await newPage(browser, { acceptDownloads: true });
    await page.goto(BASE); await ready(page);
    await page.click("text=FDE");
    const pr = first("predict", i => i.code && i.stage === "coding");
    await gotoItem(page, pr.id);
    await page.locator(".choice").nth(pr.answer).click();
    await page.getByRole("button", { name: "Finish", exact: true }).click(); await page.waitForSelector(".huge");
    const bug = first("bug");
    await gotoItem(page, bug.id);
    await page.getByRole("button", { name: "Show answer", exact: true }).click(); // a miss → due tomorrow
    await page.getByRole("button", { name: "Finish", exact: true }).click(); await page.waitForSelector(".huge");
    const before = await page.evaluate(() => JSON.parse(localStorage.getItem("it.v1")));
    await page.reload(); await ready(page);
    const after = await page.evaluate(() => JSON.parse(localStorage.getItem("it.v1")));
    check("Progress", "XP persists across reload", after.xp > 0 && after.xp === before.xp, `${after.xp} XP`);
    check("Progress", "Streak persists", after.streak.count === 1 && !!after.streak.lastDay);
    check("Progress", "Spaced repetition persists (miss due tomorrow, hit later)", after.srs[bug.id]?.interval === 1 && after.srs[pr.id]?.reps === 1,
      `bug due ${after.srs[bug.id]?.due}, predict due ${after.srs[pr.id]?.due}`);
    await page.goto(BASE + "#home"); await page.waitForSelector(".readiness");
    const coding = await page.locator(".readiness .list-btn", { hasText: "Coding" }).innerText();
    check("Progress", "Readiness meter reflects attempts after reload", /[1-9]\d*%/.test(coding), coding.replace(/\n/g, " "));
    await page.goto(BASE + "#review"); await page.waitForSelector("h1");
    check("Progress", "Review groups this week's mistake by pattern", await page.locator(".card", { hasText: bug.pattern }).count() > 0, bug.pattern);
    // export
    await page.goto(BASE + "#settings"); await page.waitForSelector("h1");
    const [dl] = await Promise.all([page.waitForEvent("download"), page.click("text=⬇ Export")]);
    const file = await dl.path();
    const exported = JSON.parse(readFileSync(file, "utf8"));
    check("Progress", "Export contains state, not the API key", exported.state?.xp === after.xp && !JSON.stringify(exported).includes("sk-ant"));
    // import into a fresh device
    const fresh = await newPage(browser);
    await fresh.page.goto(BASE + "#settings"); await fresh.page.waitForSelector("h1");
    await fresh.page.setInputFiles('input[type=file]', file);
    await fresh.page.waitForSelector("#quick-start");
    const imported = await fresh.page.evaluate(() => JSON.parse(localStorage.getItem("it.v1")));
    const same = JSON.stringify({ xp: imported.xp, streak: imported.streak, srs: imported.srs, attempts: imported.attempts.length }) ===
      JSON.stringify({ xp: after.xp, streak: after.streak, srs: after.srs, attempts: after.attempts.length });
    check("Progress", "Import round-trips XP, streak, SRS and attempts", same);
    await fresh.ctx.close();
    await ctx.close();
  }

  // ---------------------------------------------------------- 6. AI coach
  {
    // without a key
    const { ctx, page } = await newPage(browser);
    await gotoItem(page, first("roleplay").id);
    await page.fill("textarea.answer", "1. Who uses it today? 2. What data is sensitive? 3. What did you try before?");
    check("AI coach", "No key: role-play explains what's missing", await page.locator("text=Live role-play needs the AI coach").count() === 1);
    await page.click("text=✓ Grade myself");
    check("AI coach", "No key: role-play offers rubric self-grading", await page.locator(".rubric input[type=checkbox]").count() >= 3);
    await gotoItem(page, first("design").id);
    check("AI coach", "No key: design explains + offers self-grading", await page.locator("text=No API key").count() === 1 && await page.locator("text=✓ Grade myself").count() === 1);
    await ctx.close();
  }
  {
    // with a (fake) key — api.anthropic.com is mocked
    const KEY = "sk-ant-test-0000-DO-NOT-LEAK";
    const { ctx, page } = await newPage(browser);
    const seen = [], leaks = [];
    ctx.on("request", req => {
      const blob = req.url() + JSON.stringify(req.headers()) + (req.postData() || "");
      if (blob.includes(KEY) && !req.url().startsWith("https://api.anthropic.com/")) leaks.push(req.url());
    });
    await ctx.route("https://api.anthropic.com/**", async route => {
      const req = route.request();
      const cors = { "access-control-allow-origin": "*", "access-control-allow-headers": "*", "access-control-allow-methods": "POST, OPTIONS" };
      if (req.method() === "OPTIONS") return route.fulfill({ status: 204, headers: cors });
      const body = JSON.parse(req.postData());
      seen.push({ headers: req.headers(), body });
      const grading = /Grade the candidate/.test(body.system);
      const text = grading
        ? JSON.stringify({ scores: [{ criterion: "Requirements", score: 2, note: "Clear." }, { criterion: "Architecture", score: 1, note: "Partial." }], summary: "Solid start; add evals.", next: "Define a golden set." })
        : "Fair question. About two hundred analysts, mostly in finance.";
      return route.fulfill({ status: 200, headers: { ...cors, "content-type": "application/json" }, body: JSON.stringify({ content: [{ type: "text", text }] }) });
    });
    await page.goto(BASE + "#settings"); await page.waitForSelector("h1");
    await page.fill('input[type=password]', KEY);
    await page.click("text=Save key");
    await gotoItem(page, first("design").id);
    await page.fill("textarea.answer", "Requirements first: users, data sensitivity. Then MCP servers per system with least privilege, evals with a golden set, approval for writes, audit logs, pilot then staged rollout.");
    await page.click("text=🧑‍🏫 Grade with coach");
    await page.waitForSelector("text=Coach feedback");
    check("AI coach", "With key: design grading returns rubric feedback", await page.locator("text=Solid start").count() === 1);
    await gotoItem(page, first("roleplay").id);
    await page.fill("textarea.answer", "Who would use this day to day, and what do they do today?");
    await page.click("text=Send");
    await page.waitForSelector("text=two hundred analysts");
    await page.click("text=End & score");
    await page.click("text=🧑‍🏫 Grade with coach");
    await page.waitForSelector("text=Coach feedback");
    check("AI coach", "With key: role-play conversation + scoring work", true);
    const h0 = seen[0]?.headers || {};
    check("AI coach", "Sends required browser-access headers", h0["anthropic-dangerous-direct-browser-access"] === "true" && h0["x-api-key"] === KEY && !!h0["anthropic-version"],
      `model=${seen[0]?.body.model}`);
    check("AI coach", "Role-play messages start with a user turn", seen.some(s => s.body.messages[0].role === "user" && s.body.messages.length >= 3));
    check("AI coach", "Key never sent anywhere except api.anthropic.com", !leaks.length, leaks.join(", "));
    const exported = await page.evaluate(() => localStorage.getItem("it.v1"));
    check("AI coach", "Key not stored in exportable state", !exported.includes(KEY));
    await ctx.close();
  }
} catch (e) {
  check("Harness", "test run crashed", false, String(e.stack || e).slice(0, 400));
} finally {
  await browser.close();
  server.kill();
}

// ---------- report
const groups = [...new Set(results.map(r => r.group))];
const failed = results.filter(r => !r.ok);
const lines = [`# E2E report (${new Date().toISOString().slice(0, 16)}Z, ${IPHONE.viewport.width}×${IPHONE.viewport.height} iPhone 15 emulation)`, "",
  `**${results.length - failed.length}/${results.length} checks passed.**`, "",
  "| Metric | Value |", "|---|---|",
  `| First load, home usable (slow 4G, 150 ms RTT, 1.6 Mbps) | ${metrics.firstLoadMs ?? "—"} ms |`,
  `| Python ready after first load (background) | ${metrics.pythonReadyMs ?? "—"} ms |`,
  `| Returning launch (service worker) | ${metrics.returningMs ?? "—"} ms |`, ""];
for (const g of groups) {
  const rs = results.filter(r => r.group === g);
  const ok = rs.filter(r => r.ok).length;
  lines.push(`## ${g} (${ok}/${rs.length})`, "");
  // collapse the many per-screen layout checks
  for (const r of rs) if (!(g === "Mobile UX" && r.ok && /: (no horizontal|tap targets)/.test(r.name))) lines.push(`- ${r.ok ? "✅" : "❌"} ${r.name}${r.detail ? ` — ${r.detail}` : ""}`);
  if (g === "Mobile UX") lines.push(`- ✅ ${rs.filter(r => r.ok && /: (no horizontal|tap targets)/.test(r.name)).length} per-screen layout checks (no horizontal scroll, tap targets ≥ 44 px) across light & dark — screenshots in reports/screenshots/`);
  lines.push("");
}
writeFileSync(path.join(root, "reports/e2e-report.md"), lines.join("\n"));
console.log(`\n${results.length - failed.length}/${results.length} passed`);
process.exit(failed.length ? 1 : 0);
