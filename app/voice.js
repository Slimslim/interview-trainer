// Voice in and out.
//  * Record: MediaRecorder keeps the audio on the device (IndexedDB) so you can
//    replay your answer; at the same time the Web Speech API (when the browser
//    has it) transcribes into the text box. Without it, iOS keyboard dictation
//    (the mic key) fills the box instead.
//  * Speak: speechSynthesis reads feedback and role-play lines aloud.
import { h, toast } from "./ui.js";
import * as store from "./store.js";

const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
export const canTranscribe = !!SR;
export const canRecord = !!(navigator.mediaDevices?.getUserMedia && window.MediaRecorder);

export function speak(text, { force = false } = {}) {
  if (!("speechSynthesis" in window)) return;
  if (!force && !store.get().profile.voice) return;
  try {
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(String(text).replace(/[`*#]/g, ""));
    u.rate = 1.05;
    speechSynthesis.speak(u);
  } catch { /* ignore */ }
}
export const stopSpeaking = () => { try { speechSynthesis.cancel(); } catch { /* ignore */ } };

// A record/dictate control bound to a textarea.
export function voiceInput(textarea, itemId, { onFinal } = {}) {
  let rec = null, media = null, chunks = [], recog = null, baseText = "";
  const btn = h("button.rec", { type: "button", "aria-label": "Record answer" }, "🎙 Record");
  const player = h("div.grow");
  const hint = h("span.small.muted", canTranscribe ? "" : "Tip: tap the 🎤 on your keyboard to dictate.");

  async function startRec() {
    baseText = textarea.value ? textarea.value.trimEnd() + " " : "";
    if (canRecord) {
      try {
        media = await navigator.mediaDevices.getUserMedia({ audio: true });
        rec = new MediaRecorder(media);
        chunks = [];
        rec.ondataavailable = e => e.data.size && chunks.push(e.data);
        rec.onstop = async () => {
          media.getTracks().forEach(t => t.stop());
          const blob = new Blob(chunks, { type: rec.mimeType || "audio/mp4" });
          await store.saveRecording(itemId, blob);
          player.replaceChildren(h("audio", { controls: true, src: URL.createObjectURL(blob) }));
        };
        rec.start();
      } catch (e) {
        toast("Microphone unavailable — use keyboard dictation instead.");
        rec = null;
      }
    }
    if (SR) {
      try {
        recog = new SR();
        recog.continuous = true;
        recog.interimResults = true;
        recog.lang = navigator.language || "en-US";
        recog.onresult = e => {
          let txt = "";
          for (const r of e.results) txt += r[0].transcript;
          textarea.value = baseText + txt;
          textarea.dispatchEvent(new Event("input"));
        };
        recog.onerror = () => {};
        recog.start();
      } catch { recog = null; }
    }
    if (!rec && !recog) return;
    btn.classList.add("on");
    btn.textContent = "■ Stop";
  }

  function stopRec() {
    try { rec && rec.state !== "inactive" && rec.stop(); } catch { /* ignore */ }
    try { recog && recog.stop(); } catch { /* ignore */ }
    rec = null; recog = null;
    btn.classList.remove("on");
    btn.textContent = "🎙 Record";
    onFinal && onFinal(textarea.value);
  }

  btn.onclick = () => (btn.classList.contains("on") ? stopRec() : startRec());
  if (!canRecord && !canTranscribe) btn.disabled = true;
  return h("div.voice", btn, hint, player);
}
