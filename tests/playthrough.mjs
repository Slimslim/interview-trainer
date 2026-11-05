// Self-review: plays 3 full sessions as the learner would and screenshots
// every step to reports/playthrough/. Not a pass/fail test — it's for
// eyeballing friction.   node tests/playthrough.mjs
import { createRequire } from "node:module";
import { spawn } from "node:child_process";
import { readFileSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium, devices } = require("playwright");
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const OUT = path.join(root, "reports/playthrough");
rmSync(OUT, { recursive: true, force: true }); mkdirSync(OUT, { recursive: true });
const PORT = 8797, BASE = `http://localhost:${PORT}/`;
const ITEMS = {};
for (const id of ["comeback", "anthropic-fde", "anthropic-applied-ai-architect"]) {
  const m = JSON.parse(readFileSync(path.join(root, `packs/${id}/pack.json`)));
  for (const f of m.files) for (const it of JSON.parse(readFileSync(path.join(root, `packs/${id}/${f}`))).items) ITEMS[it.id] = it;
}
const log = [];
let n = 0;
const shot = async (page, label) => { n++; await page.screenshot({ path: path.join(OUT, `${String(n).padStart(3, "0")}-${label}.png`) }); };

async function playItem(page, s) {
  const id = await page.locator("section[data-item]").getAttribute("data-item");
  const it = ITEMS[id];
  const t0 = Date.now();
  await shot(page, `${s}-${it.type}-start`);
  const btn = name => page.getByRole("button", { name, exact: true });
  if (it.type === "code" || it.type === "challenge") {
    const step = it.type === "challenge" ? it.steps[0] : it;
    await btn("▶ Run tests").click();               // run the starter first, like a person would
    await page.waitForSelector(".feedback", { timeout: 60000 });
    await btn("💡 Hint 1/3").click();
    await page.locator("textarea.editor").fill(step.solution);
    await btn("▶ Run tests").click();
    await page.waitForSelector("text=/All \\d+ tests pass/", { timeout: 30000 });
    if (it.type === "challenge") await shot(page, `${s}-challenge-level1-done`);
    const stop = page.getByRole("button", { name: "Stop here", exact: true });
    if (await stop.count()) { await stop.click(); log.push(`${s}: challenge  ${id.padEnd(40)} level 1 passed, stopped`); return; }
  } else if (it.type === "predict") {
    await page.locator(".choice").nth(it.answer).click();
  } else if (it.type === "parsons") {
    for (const line of it.lines) await page.locator(".parsons-list:not(.dropzone) .pline", { hasText: line.trim() }).first().click();
    await btn("Check order").click();
  } else if (it.type === "bug") {
    await page.locator(".codeline").nth(it.bugLine - 1).click();
    await page.locator("textarea.editor").fill(it.fixed);
    await btn("▶ Run tests with my fix").click();
    await page.waitForSelector("text=Fixed — all tests pass", { timeout: 30000 });
  } else if (it.type === "flashcard") {
    await btn("Show answer").click(); await btn("Good").click();
  } else if (["behavioral", "design", "roleplay"].includes(it.type)) {
    await page.locator("textarea.answer").fill("Situation: at a laser equipment customer in Shenzhen, throughput dropped 30 %. I ran discovery, found the root cause, piloted a fix, and cut downtime by 40 % in 6 weeks. I'd involve their quality team earlier next time.");
    await btn("✓ Grade myself").click();
    const boxes = page.locator(".rubric input[type=checkbox]");
    for (let i = 0; i < Math.min(3, await boxes.count()); i++) await boxes.nth(i).check();
    await btn("Done").click();
  }
  await page.waitForTimeout(200);
  await shot(page, `${s}-${it.type}-done`);
  log.push(`${s}: ${it.type.padEnd(10)} ${id.padEnd(40)} ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  const next = page.getByRole("button", { name: /Next →|Finish/ }).last();
  await next.click();
}

async function playSession(page, s) {
  while (await page.locator("section[data-item]").count()) await playItem(page, s);
  await page.waitForSelector(".huge");
  await shot(page, `${s}-summary`);
  log.push(`${s}: summary — ${(await page.locator(".huge").innerText())}`);
  await page.getByRole("button", { name: "Home", exact: true }).click();
}

const server = spawn(process.execPath, [path.join(root, "tools/serve.mjs"), String(PORT)], { stdio: "pipe" });
await new Promise(r => server.stdout.once("data", r));
const browser = await chromium.launch();
const ctx = await browser.newContext({ ...devices["iPhone 15"] });
const page = await ctx.newPage();
page.on("pageerror", e => log.push("PAGE ERROR " + e));
try {
  await page.goto(BASE);
  await page.waitForSelector("#quick-start");
  await shot(page, "s1-home");
  // Session 1: brand new, Comeback track, 5 min
  await page.click("#quick-start");
  await playSession(page, "s1");
  await shot(page, "s1-home-after");
  // Session 2: FDE track, 10 min, gates skipped (as if Comeback were done)
  await page.goto(BASE + "#settings");
  await page.getByText("Skip gates").click();
  await page.goto(BASE + "#home");
  await page.getByRole("button", { name: "FDE", exact: true }).click();
  await page.getByRole("button", { name: "10 min", exact: true }).click();
  await page.click("#quick-start");
  await playSession(page, "s2");
  // Session 3: full mock round — coding
  await page.goto(BASE + "#modes");
  await page.locator("summary", { hasText: "Coding" }).click();
  await shot(page, "s3-mock-picker");
  await page.locator("details[open] >> text=Start mock").click();
  await playSession(page, "s3");
  await page.goto(BASE + "#review");
  await shot(page, "review");
} catch (e) {
  log.push("CRASH " + e.message.split("\n")[0]);
  await shot(page, "crash");
} finally {
  await browser.close(); server.kill();
}
writeFileSync(path.join(OUT, "log.txt"), log.join("\n"));
console.log(log.join("\n"));
