// Optional AI coach. Calls the Claude Messages API straight from the browser
// with the key saved in Settings. The key is only ever sent to api.anthropic.com.
import * as store from "./store.js";

export const API_URL = "https://api.anthropic.com/v1/messages";
// Model IDs from Anthropic's models overview (checked 2026-11-05).
export const MODELS = [
  { id: "claude-sonnet-5-5", label: "Sonnet 5.5 (balanced, default)" },
  { id: "claude-opus-5-5", label: "Opus 5.5 (deepest feedback)" },
  { id: "claude-haiku-5-5", label: "Haiku 5.5 (fastest, cheapest)" },
];

export const hasKey = () => !!store.getApiKey();

export async function ask({ system, messages, maxTokens = 900 }) {
  const key = store.getApiKey();
  if (!key) throw new Error("No API key — add one in Settings.");
  if (!navigator.onLine) throw new Error("You're offline — the coach needs a connection.");
  const res = await fetch(API_URL, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-api-key": key,
      "anthropic-version": "2023-06-01",
      // Required by Anthropic for calls made directly from a browser (CORS).
      "anthropic-dangerous-direct-browser-access": "true",
    },
    body: JSON.stringify({ model: store.get().profile.model, max_tokens: maxTokens, system, messages }),
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body?.error?.message || `Claude API error ${res.status}`);
  return (body.content || []).filter(b => b.type === "text").map(b => b.text).join("\n").trim();
}

// Parse model output that should be JSON: strip ``` fences, take the outermost
// {...}, and validate it's an object. (Yes — exactly what the bug drills teach.)
export function parseJSON(text) {
  const t = String(text).replace(/```(?:json)?/g, "");
  const start = t.indexOf("{"), end = t.lastIndexOf("}");
  if (start < 0 || end <= start) return null;
  try {
    const v = JSON.parse(t.slice(start, end + 1));
    return v && typeof v === "object" ? v : null;
  } catch { return null; }
}

const GRADER = `You are a demanding but kind interview coach for Anthropic roles (Forward Deployed Engineer, Applied AI Architect).
Grade the candidate's answer against the rubric. Be specific, quote their words, and name what's missing.
Reply with ONLY a JSON object:
{"scores":[{"criterion":"...","score":0-2,"note":"one sentence"}],"summary":"2-3 sentences, spoken style, second person","next":"the single most useful thing to practise next"}
Scores: 0 = missing, 1 = partial, 2 = strong.`;

export async function gradeRubric({ prompt, answer, rubric, extra = "" }) {
  const text = await ask({
    system: GRADER,
    messages: [{
      role: "user",
      content: `QUESTION / SCENARIO:\n${prompt}\n\nRUBRIC:\n${rubric.map(r => `- ${r.criterion}: ${r.lookFor}`).join("\n")}\n${extra}\n\nCANDIDATE ANSWER:\n${answer || "(empty)"}`,
    }],
  });
  const j = parseJSON(text);
  if (!j || !Array.isArray(j.scores)) return { scores: [], summary: text, next: "" };
  return j;
}

export function rubricScore(rubric, scores) {
  let total = 0, got = 0;
  rubric.forEach((r, i) => {
    const w = r.weight || 1;
    total += 2 * w;
    const s = scores.find(s => s.criterion === r.criterion) || scores[i];
    got += w * Math.max(0, Math.min(2, +(s?.score ?? 0)));
  });
  return total ? got / total : 0;
}

export async function suggestStory(question, stories) {
  if (!stories.length) return null;
  const text = await ask({
    system: "You match interview questions to a candidate's STAR stories. Reply ONLY JSON: {\"id\":\"best story id\",\"why\":\"one sentence\",\"angle\":\"how to frame it for this question, one sentence\"}",
    messages: [{ role: "user", content: `Question: ${question}\n\nStories:\n${stories.map(s => `[${s.id}] ${s.title}: ${s.situation} / ${s.action} / ${s.result}`).join("\n")}` }],
    maxTokens: 300,
  });
  return parseJSON(text);
}

export async function reviewCode({ prompt, code, solved, tests }) {
  return ask({
    system: `You are a Python interview coach. The candidate is rebuilding hand-coding skills and learns by doing.
${solved ? "They solved it. Give 3 short bullets: readability, idiomatic Python, complexity. Then one interview-style follow-up question." : "They have NOT solved it yet. Never write the solution or corrected code. Give one Socratic nudge (max 2 sentences) pointing at the most important problem."}`,
    messages: [{ role: "user", content: `Task:\n${prompt}\n\nTheir code:\n${code}\n\nTest results:\n${tests}` }],
    maxTokens: 400,
  });
}
