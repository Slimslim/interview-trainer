// Tiny DOM helpers. h("button.primary", {onclick}, "Go") -> <button class="primary">
export function h(tag, attrs, ...children) {
  const [name, ...classes] = tag.split(".");
  const el = document.createElement(name || "div");
  if (classes.length) el.className = classes.join(" ");
  if (attrs && (typeof attrs !== "object" || attrs instanceof Node || Array.isArray(attrs))) {
    children.unshift(attrs);
    attrs = null;
  }
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v == null || v === false) continue;
    if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
    else if (k === "html") el.innerHTML = v;
    else if (k === "style" && typeof v === "object") Object.assign(el.style, v);
    else if (k in el && typeof v !== "string") el[k] = v;
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const c of children.flat(Infinity)) {
    if (c == null || c === false) continue;
    el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return el;
}

export function mount(...nodes) {
  const app = document.getElementById("app");
  app.replaceChildren(...nodes);
  window.scrollTo(0, 0);
}

export function toast(text, ms = 2600) {
  const t = h("div.toast", { role: "status" }, text);
  document.body.append(t);
  setTimeout(() => t.remove(), ms);
}

const esc = s => s.replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

// Minimal markdown: `code`, **bold**, ```blocks```, paragraphs and "- " lists.
export function md(text = "") {
  const parts = String(text).split(/```(?:\w+)?\n?([\s\S]*?)```/g);
  const out = parts.map((p, i) => {
    if (i % 2) return `<pre>${esc(p.replace(/\n$/, ""))}</pre>`;
    return p.split(/\n{2,}/).map(block => {
      const inline = s => esc(s).replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>");
      const lines = block.trim().split("\n");
      if (lines.every(l => /^\s*[-*] /.test(l)) && lines[0]) {
        return "<ul>" + lines.map(l => `<li>${inline(l.replace(/^\s*[-*] /, ""))}</li>`).join("") + "</ul>";
      }
      return block.trim() ? `<p>${lines.map(inline).join("<br>")}</p>` : "";
    }).join("");
  });
  return h("div.md", { html: out.join("") });
}

export const pre = code => h("pre", String(code).replace(/\n$/, ""));

export function fmtTime(sec) {
  sec = Math.max(0, Math.round(sec));
  return `${Math.floor(sec / 60)}:${String(sec % 60).padStart(2, "0")}`;
}

export function shuffle(arr, rnd = Math.random) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rnd() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

export function download(filename, text) {
  const url = URL.createObjectURL(new Blob([text], { type: "application/json" }));
  const a = h("a", { href: url, download: filename });
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
