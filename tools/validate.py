#!/usr/bin/env python3
"""Content validator.

Checks every pack under packs/ (listed in packs/index.json):
  * JSON schema (schema/pack.schema.json), unique ids, stage references
  * code / challenge steps: reference solution passes all tests, starter fails >= 1
    (challenge step N>1: the step N-1 solution must fail step N's tests, which
     proves each step really adds a requirement)
  * bug: buggy snippet fails its tests, fixed version passes, bugLine changed
  * parsons: lines in the given order pass the tests
  * predict (kind=output): running the code prints exactly the marked answer
  * research/*.md: every confirmed/reported claim cites a source that has a URL

Writes the execution jobs to reports/jobs.json so tools/validate-pyodide.mjs
can re-run the same checks inside Pyodide.

Usage:  python3 tools/validate.py [--pack ID] [--no-exec]
"""
import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

RUNNER = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
import harness
job = json.load(sys.stdin)
if job["kind"] == "run_tests":
    r = harness.run_sync(harness.run_tests(job["code"], job["tests"]))
else:
    r = harness.run_sync(harness.run_code(job["code"]))
print(json.dumps(r))
"""

errors = []


def err(where, msg):
    errors.append(f"{where}: {msg}")


def load_json(path):
    try:
        return json.loads(path.read_text())
    except Exception as e:  # noqa: BLE001
        err(str(path.relative_to(ROOT)), f"invalid JSON: {e}")
        return None


def schema_check(packs):
    try:
        import jsonschema
    except ImportError:
        err("schema", "pip install jsonschema")
        return
    schema = json.loads((ROOT / "schema/pack.schema.json").read_text())
    validator = jsonschema.Draft202012Validator(schema)
    for pack in packs:
        for rel, doc in pack["docs"].items():
            for e in sorted(validator.iter_errors(doc), key=lambda e: list(e.path))[:5]:
                loc = "/".join(str(p) for p in e.path)
                # oneOf errors are noisy; show the best sub-error
                best = jsonschema.exceptions.best_match([e])
                err(rel, f"schema at {loc}: {best.message[:200]}")


def collect_jobs(packs):
    jobs = []
    for pack in packs:
        for it in pack["items"]:
            iid = it["id"]
            t = it["type"]
            if t == "code":
                jobs.append(dict(id=iid, what="solution passes", kind="run_tests",
                                 code=it["solution"], tests=it["tests"], expect="pass"))
                jobs.append(dict(id=iid, what="starter fails", kind="run_tests",
                                 code=it.get("starter", ""), tests=it["tests"], expect="fail"))
            elif t == "challenge":
                prev = None
                for n, st in enumerate(it["steps"], 1):
                    jobs.append(dict(id=iid, what=f"step {n} solution passes", kind="run_tests",
                                     code=st["solution"], tests=st["tests"], expect="pass"))
                    starter = st.get("starter")
                    if starter is None:
                        starter = prev if prev is not None else ""
                    jobs.append(dict(id=iid, what=f"step {n} starter fails", kind="run_tests",
                                     code=starter, tests=st["tests"], expect="fail"))
                    if prev is not None and st.get("starter") is not None:
                        jobs.append(dict(id=iid, what=f"step {n-1} solution fails step {n}",
                                         kind="run_tests", code=prev, tests=st["tests"],
                                         expect="fail"))
                    prev = st["solution"]
            elif t == "bug":
                jobs.append(dict(id=iid, what="buggy fails", kind="run_tests",
                                 code=it["code"], tests=it["tests"], expect="fail"))
                jobs.append(dict(id=iid, what="fixed passes", kind="run_tests",
                                 code=it["fixed"], tests=it["tests"], expect="pass"))
            elif t == "parsons":
                jobs.append(dict(id=iid, what="parsons solution passes", kind="run_tests",
                                 code="\n".join(it["lines"]) + "\n", tests=it["tests"],
                                 expect="pass"))
            elif t == "predict" and it["kind"] == "output":
                jobs.append(dict(id=iid, what="output matches answer", kind="run_code",
                                 code=it["code"], expect="stdout",
                                 answer=it["choices"][it["answer"]],
                                 others=[c for i, c in enumerate(it["choices"]) if i != it["answer"]]))
    return jobs


def judge(job, r):
    """Return None if the job met expectations, else a message. Shared logic
    with validate-pyodide.mjs (keep in sync)."""
    if job["expect"] == "pass":
        if not r["ok"]:
            bad = r["error"] or "; ".join(f'{t["name"]}: {t["message"][:120]}'
                                          for t in r["tests"] if not t["passed"])
            return f"expected pass, got: {bad or 'no tests found'}"
    elif job["expect"] == "fail":
        if r["ok"]:
            return "expected at least one failing test, all passed"
        if not r["tests"] and r["error"] and r["error"].startswith("Test setup failed"):
            return f"tests themselves broken: {r['error']}"
    elif job["expect"] == "stdout":
        got = r["stdout"].strip() if r["ok"] else f"error: {r['error'].splitlines()[-1]}"
        want = job["answer"].strip()
        if r["ok"]:
            if got != want:
                return f"printed {got!r}, answer says {want!r}"
        else:
            exc = r["error"].splitlines()[-1].split(":")[0]
            if exc not in want:
                return f"raised {exc}, answer says {want!r}"
        for o in job["others"]:
            if o.strip() == want:
                return "duplicate choice equals the answer"
    return None


def run_job(job):
    try:
        p = subprocess.run([sys.executable, "-I", "-c", RUNNER, str(ROOT / "app")],
                           input=json.dumps(job), capture_output=True, text=True, timeout=15)
        r = json.loads(p.stdout.strip().splitlines()[-1])
    except subprocess.TimeoutExpired:
        if job["expect"] == "fail":
            return None  # an infinite loop in starter code counts as failing
        return "timed out"
    except Exception as e:  # noqa: BLE001
        return f"runner crashed: {e} {p.stderr[-300:] if 'p' in dir() else ''}"
    return judge(job, r)


def structure_check(packs):
    seen = Counter()
    for pack in packs:
        stage_ids = {s["id"] for s in pack["manifest"].get("stages", [])}
        for it in pack["items"]:
            seen[it["id"]] += 1
            where = f'{pack["id"]}/{it["id"]}'
            if it.get("stage") not in stage_ids:
                err(where, f'stage {it.get("stage")!r} not in pack stages {sorted(stage_ids)}')
            if pack["manifest"].get("kind") == "comeback" and "week" not in it:
                err(where, "comeback item needs a week")
            if it["type"] in ("bug", "predict") and it["answer"] >= len(it["choices"]):
                err(where, "answer index out of range")
            if it["type"] == "bug":
                bl, fl = it["code"].splitlines(), it["fixed"].splitlines()
                if it["bugLine"] > len(bl):
                    err(where, "bugLine beyond snippet")
                elif it["bugLine"] <= len(fl) and bl[it["bugLine"] - 1] == fl[it["bugLine"] - 1] \
                        and len(bl) == len(fl):
                    err(where, "bugLine is identical in fixed version")
                if len(bl) > 25:
                    err(where, f"snippet too long for a phone ({len(bl)} lines > 25)")
            if it["type"] == "parsons" and len(set(it["lines"])) != len(it["lines"]):
                err(where, "parsons lines must be unique (add a comment to disambiguate)")
        for rule in pack["manifest"].get("reuse", []):
            for src_stage, dst in rule["stageMap"].items():
                if dst not in stage_ids:
                    err(pack["id"], f"reuse maps to unknown stage {dst}")
    for iid, n in seen.items():
        if n > 1:
            err(iid, f"duplicate id ({n}x)")


def research_check(research_files):
    for path in research_files:
        rel = str(path.relative_to(ROOT))
        text = path.read_text()
        defined = {}
        for m in re.finditer(r"^\|\s*\[?([A-Z]\d+)\]?\s*\|(.*)$", text, re.M):
            defined[m.group(1)] = m.group(2)
        for sid, row in defined.items():
            if "http" not in row:
                err(rel, f"source {sid} has no URL")
            if not re.search(r"confirmed|reported", row, re.I):
                err(rel, f"source {sid} not marked confirmed/reported")
        if not defined:
            err(rel, "no sources table (| S1 | ... | url | date | confirmed/reported |)")
        in_table = re.compile(r"^\|\s*\[?[A-Z]\d+")
        for n, line in enumerate(text.splitlines(), 1):
            if in_table.match(line):
                continue
            if re.search(r"\((confirmed|reported)\b", line, re.I):
                refs = re.findall(r"\[([A-Z]\d+)\]", line)
                if not refs and "http" not in line:
                    err(f"{rel}:{n}", "claim without source reference")
                for r_ in refs:
                    if r_ not in defined:
                        err(f"{rel}:{n}", f"cites undefined source {r_}")


def load_packs(only=None, files=None):
    index = load_json(ROOT / "packs/index.json") or {"packs": []}
    packs = []
    for pid in index["packs"]:
        if only and pid not in only:
            continue
        pdir = ROOT / "packs" / pid
        manifest = load_json(pdir / "pack.json")
        if manifest is None:
            continue
        docs = {f"packs/{pid}/pack.json": manifest}
        items = []
        for f in manifest.get("files", []):
            if files and f not in files:
                continue
            doc = load_json(pdir / f)
            if doc is None:
                continue
            docs[f"packs/{pid}/{f}"] = doc
            items += doc.get("items", [])
        packs.append(dict(id=pid, manifest=manifest, docs=docs, items=items))
    return packs, index


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", action="append")
    ap.add_argument("--no-exec", action="store_true")
    ap.add_argument("--file", action="append",
                    help="only check items from this file (e.g. bugs.json); others may be missing")
    args = ap.parse_args()

    packs, index = load_packs(args.pack, args.file)
    schema_check(packs)
    structure_check(packs)
    research = []
    for pack in packs:
        r = pack["manifest"].get("research")
        if r:
            if not (ROOT / r).exists():
                err(pack["id"], f"research file {r} missing")
            else:
                research.append(ROOT / r)
    research_check(research)

    jobs = collect_jobs(packs)
    (ROOT / "reports").mkdir(exist_ok=True)
    if not args.file:
        (ROOT / "reports/jobs.json").write_text(json.dumps(jobs))
    if not args.no_exec:
        with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as ex:
            for job, msg in zip(jobs, ex.map(run_job, jobs)):
                if msg:
                    err(job["id"], f'{job["what"]}: {msg}')

    print("Content summary")
    for pack in packs:
        c = Counter(i["type"] for i in pack["items"])
        weeks = Counter(i.get("week") for i in pack["items"] if i.get("week"))
        extra = f"  weeks={dict(sorted(weeks.items()))}" if weeks else ""
        print(f'  {pack["id"]:34} {len(pack["items"]):4} items  {dict(sorted(c.items()))}{extra}')
    print(f"  execution checks: {0 if args.no_exec else len(jobs)} (CPython {sys.version.split()[0]})")
    print(f"  research files checked: {len(research)}")
    if errors:
        print(f"\nFAILED: {len(errors)} problem(s)")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print("\nALL CONTENT CHECKS PASSED")


if __name__ == "__main__":
    main()
