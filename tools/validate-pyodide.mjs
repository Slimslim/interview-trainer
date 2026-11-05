// Re-runs the execution checks from reports/jobs.json inside Pyodide
// (the same Python runtime the phone uses). Run tools/validate.py first.
//   node tools/validate-pyodide.mjs
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const { loadPyodide } = await import(path.join(root, "vendor/pyodide/pyodide.mjs"));
const py = await loadPyodide({ indexURL: path.join(root, "vendor/pyodide") + "/" });
py.FS.writeFile("/home/pyodide/harness.py", readFileSync(path.join(root, "app/harness.py"), "utf8"));
await py.runPythonAsync("import sys; sys.path.insert(0, '/home/pyodide'); import harness, json");

const jobs = JSON.parse(readFileSync(path.join(root, "reports/jobs.json"), "utf8"));

// Mirror of judge() in validate.py
function judge(job, r) {
  if (job.expect === "pass" && !r.ok) {
    const bad = r.error || r.tests.filter(t => !t.passed).map(t => `${t.name}: ${t.message.slice(0, 120)}`).join("; ");
    return `expected pass, got: ${bad || "no tests found"}`;
  }
  if (job.expect === "fail" && r.ok) return "expected at least one failing test, all passed";
  if (job.expect === "stdout") {
    const want = job.answer.trim();
    if (r.ok && r.stdout.trim() !== want) return `printed ${JSON.stringify(r.stdout.trim())}, answer says ${JSON.stringify(want)}`;
    if (!r.ok) {
      const exc = r.error.split("\n").pop().split(":")[0];
      if (!want.includes(exc)) return `raised ${exc}, answer says ${JSON.stringify(want)}`;
    }
  }
  return null;
}

const failures = [];
const t0 = Date.now();
for (const job of jobs) {
  py.globals.set("JOB", JSON.stringify(job));
  // Starters with infinite loops would hang; validate.py treats a timeout as
  // a failing starter, so skip "fail" jobs that time out in CPython by
  // running them with a step budget via sys.settrace.
  const code = job.kind === "run_tests"
    ? `j = json.loads(JOB)\nimport sys\n_n=[0]\ndef _tr(f,e,a):\n    _n[0]+=1\n    if _n[0]>2_000_000: raise TimeoutError('step budget')\n    return _tr\nsys.settrace(_tr)\ntry:\n    _r = await harness.run_tests(j['code'], j['tests'])\nfinally:\n    sys.settrace(None)\njson.dumps(_r)`
    : `j = json.loads(JOB)\njson.dumps(await harness.run_code(j['code']))`;
  const r = JSON.parse(await py.runPythonAsync(code));
  const msg = judge(job, r);
  if (msg) failures.push(`${job.id}: ${job.what}: ${msg}`);
}
console.log(`Pyodide ${py.version}: ${jobs.length} execution checks in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
if (failures.length) {
  console.log(`FAILED: ${failures.length}`);
  failures.forEach(f => console.log("  - " + f));
  process.exit(1);
}
console.log("ALL PYODIDE CHECKS PASSED");
