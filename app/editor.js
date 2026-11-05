// A phone-friendly code editor: a plain <textarea> (works with every
// on-screen keyboard and dictation) plus a key bar with the symbols iOS
// hides behind two taps, Tab/indent handling and auto-indent after ":".
import { h } from "./ui.js";

const KEYS = ["⇥", "⇤", ":", "(", ")", "[", "]", "{", "}", "=", "\"", "'", "_", ".", ",", "#", "<", ">", "+", "-", "*", "/", "%", "!"];
const PAIRS = { "(": ")", "[": "]", "{": "}", "\"": "\"", "'": "'" };

export function codeEditor(value, { onChange, minHeight } = {}) {
  const ta = h("textarea.editor", {
    spellcheck: false, autocapitalize: "off", autocomplete: "off", autocorrect: "off",
    "aria-label": "Code editor", wrap: "off", inputmode: "text",
  });
  ta.value = value || "";
  if (minHeight) ta.style.minHeight = minHeight;
  const changed = () => onChange && onChange(ta.value);

  function insert(text, caretOffset = text.length) {
    const { selectionStart: s, selectionEnd: e, value: v } = ta;
    ta.value = v.slice(0, s) + text + v.slice(e);
    ta.selectionStart = ta.selectionEnd = s + caretOffset;
    changed();
  }
  function lineStart(pos) { return ta.value.lastIndexOf("\n", pos - 1) + 1; }
  function indent(dir) {
    const s = lineStart(ta.selectionStart);
    const v = ta.value;
    if (dir > 0) { ta.value = v.slice(0, s) + "    " + v.slice(s); ta.selectionStart = ta.selectionEnd = ta.selectionEnd + 4; }
    else {
      const m = v.slice(s).match(/^ {1,4}/);
      if (!m) return;
      const caret = ta.selectionStart;
      ta.value = v.slice(0, s) + v.slice(s + m[0].length);
      ta.selectionStart = ta.selectionEnd = Math.max(s, caret - m[0].length);
    }
    changed();
  }

  ta.addEventListener("keydown", e => {
    if (e.key === "Tab") { e.preventDefault(); indent(e.shiftKey ? -1 : 1); }
    else if (e.key === "Enter") {
      e.preventDefault();
      const s = lineStart(ta.selectionStart);
      const line = ta.value.slice(s, ta.selectionStart);
      let pad = line.match(/^\s*/)[0];
      if (/:\s*(#.*)?$/.test(line)) pad += "    ";
      insert("\n" + pad);
    }
  });
  ta.addEventListener("input", changed);

  const bar = h("div.keybar", { role: "toolbar", "aria-label": "Code symbols" },
    KEYS.map(k => h("button", {
      type: "button", "aria-label": k === "⇥" ? "Indent" : k === "⇤" ? "Dedent" : `Insert ${k}`,
      // mousedown/preventDefault keeps the keyboard open on iOS
      onpointerdown: e => e.preventDefault(),
      onclick: () => {
        ta.focus();
        if (k === "⇥") indent(1);
        else if (k === "⇤") indent(-1);
        else if (PAIRS[k] && ta.selectionStart === ta.selectionEnd) insert(k + PAIRS[k], 1);
        else insert(k);
      },
    }, k)));

  const wrap = h("div.code-editor", bar, ta);
  wrap.textarea = ta;
  Object.defineProperty(wrap, "value", { get: () => ta.value, set: v => { ta.value = v; } });
  return wrap;
}
