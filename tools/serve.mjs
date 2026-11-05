// Minimal static server for local testing: node tools/serve.mjs [port]
// (gzip like GitHub Pages/Cloudflare do, so load timings are realistic)
import http from "node:http";
import { readFile, stat } from "node:fs/promises";
import { gzipSync } from "node:zlib";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const port = +(process.argv[2] || 8080);
const TYPES = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".mjs": "text/javascript", ".css": "text/css",
  ".json": "application/json", ".webmanifest": "application/manifest+json", ".wasm": "application/wasm",
  ".zip": "application/zip", ".png": "image/png", ".svg": "image/svg+xml", ".py": "text/plain; charset=utf-8",
  ".md": "text/markdown; charset=utf-8",
};
const COMPRESS = new Set([".html", ".js", ".mjs", ".css", ".json", ".webmanifest", ".py", ".svg", ".wasm"]);

http.createServer(async (req, res) => {
  try {
    let p = decodeURIComponent(new URL(req.url, "http://x").pathname);
    if (p.endsWith("/")) p += "index.html";
    const file = path.join(root, p);
    if (!file.startsWith(root)) throw new Error("bad path");
    await stat(file);
    let body = await readFile(file);
    const ext = path.extname(file);
    const headers = { "content-type": TYPES[ext] || "application/octet-stream", "cache-control": "max-age=600" };
    if (COMPRESS.has(ext) && /gzip/.test(req.headers["accept-encoding"] || "")) {
      body = gzipSync(body);
      headers["content-encoding"] = "gzip";
    }
    res.writeHead(200, headers);
    res.end(body);
  } catch {
    res.writeHead(404, { "content-type": "text/plain" });
    res.end("not found");
  }
}).listen(port, "127.0.0.1", () => console.log(`Serving ${root} on http://localhost:${port}`));
