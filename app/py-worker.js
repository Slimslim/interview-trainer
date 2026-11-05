// Web Worker that owns Pyodide. Messages in:  {id, cmd: "run_tests"|"run_code", code, tests}
// Messages out: {ready:true} once loaded, then {id, result} per request.
import { loadPyodide } from "../vendor/pyodide/pyodide.mjs";

const base = new URL("../", import.meta.url);
let py;

const boot = (async () => {
  py = await loadPyodide({ indexURL: new URL("vendor/pyodide/", base).href });
  const harness = await (await fetch(new URL("app/harness.py", base))).text();
  py.FS.writeFile("/home/pyodide/harness.py", harness);
  await py.runPythonAsync("import sys, json\nsys.path.insert(0, '/home/pyodide')\nimport harness");
  postMessage({ ready: true, version: py.version });
})().catch(e => postMessage({ fatal: String(e) }));

onmessage = async ({ data }) => {
  await boot;
  try {
    py.globals.set("REQ", JSON.stringify(data));
    const out = await py.runPythonAsync(
      "_q = json.loads(REQ)\n" +
      "json.dumps(await (harness.run_tests(_q['code'], _q['tests']) if _q['cmd'] == 'run_tests' else harness.run_code(_q['code'])))");
    postMessage({ id: data.id, result: JSON.parse(out) });
  } catch (e) {
    postMessage({ id: data.id, result: { ok: false, error: String(e), tests: [], stdout: "" } });
  }
};
