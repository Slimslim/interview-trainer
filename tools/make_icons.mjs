// Renders icons/icon.svg to the PNG sizes iOS and Android need.
import { createRequire } from "node:module";
import { readFileSync } from "node:fs";
const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const svg = readFileSync(new URL("../icons/icon.svg", import.meta.url), "utf8");
const browser = await chromium.launch();
for (const [name, size, pad] of [["apple-touch-icon.png", 180, 0], ["icon-192.png", 192, 0], ["icon-512.png", 512, 0]]) {
  const page = await browser.newPage({ viewport: { width: size, height: size } });
  await page.setContent(`<body style="margin:0;background:#c25a2c">${svg.replace("<svg", `<svg width="${size}" height="${size}"`).replace('rx="112"', 'rx="0"')}</body>`);
  await page.screenshot({ path: new URL(`../icons/${name}`, import.meta.url).pathname });
}
await browser.close();
console.log("icons written");
