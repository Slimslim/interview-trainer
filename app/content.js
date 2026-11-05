// Loads packs/index.json, every pack manifest and its item files.
// Reuse rules let one pack borrow another pack's items with a stage mapping.
const packs = {};
let order = [];
const byId = {};
let ready = null;

async function getJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url}: ${r.status}`);
  return r.json();
}

export async function loadManifests() {
  const index = await getJSON("packs/index.json");
  order = index.packs;
  await Promise.all(index.packs.map(async id => {
    packs[id] = { id, manifest: await getJSON(`packs/${id}/pack.json`), own: [], items: [] };
  }));
  return index.packs.map(id => packs[id]);
}

export function loadItems() {
  if (ready) return ready;
  ready = (async () => {
    await Promise.all(Object.values(packs).map(async p => {
      const files = await Promise.all(p.manifest.files.map(f =>
        getJSON(`packs/${p.id}/${f}`).catch(e => { console.warn(e); return { items: [] }; })));
      p.own = files.flatMap(f => f.items).map(it => ({ ...it, pack: p.id }));
      p.own.forEach(it => { byId[it.id] = it; });
    }));
    for (const p of Object.values(packs)) {
      const reused = [];
      for (const rule of p.manifest.reuse || []) {
        const src = packs[rule.pack];
        if (!src) continue;
        for (const it of src.own) {
          if (rule.types && !rule.types.includes(it.type)) continue;
          const stage = rule.stageMap[it.stage];
          if (!stage) continue;
          reused.push({ ...it, pack: p.id, stage, reusedFrom: src.id });
        }
      }
      const ownIds = new Set(p.own.map(i => i.id));
      p.items = [...p.own, ...reused.filter(i => !ownIds.has(i.id))];
    }
    return packs;
  })();
  return ready;
}

export const allPacks = () => order.map(id => packs[id]).filter(Boolean);
export const getPack = id => packs[id];
export const getItem = id => byId[id];
export const itemsReady = () => ready;

export function stageTitle(packId, stageId) {
  const s = packs[packId]?.manifest.stages.find(s => s.id === stageId);
  return s ? s.title : stageId;
}

// Rough minutes per item type, used to fill a session of N minutes.
export const MINUTES = {
  flashcard: 0.35, predict: 0.4, bug: 1.6, parsons: 1.5, code: 2, challenge: 7,
  design: 9, roleplay: 9, behavioral: 3,
};
export function itemMinutes(it) {
  if (it.type === "challenge") return 7;
  if (it.type === "code" && it.week >= 3) return 3;
  return it.minutes || MINUTES[it.type] || 2;
}

export const TYPE_LABEL = {
  code: "Write code", challenge: "Progressive challenge", bug: "Spot the bug", predict: "Predict",
  parsons: "Parsons puzzle", flashcard: "Flashcard", design: "Design scenario",
  roleplay: "Customer role-play", behavioral: "Behavioral",
};
