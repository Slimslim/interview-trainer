#!/usr/bin/env python3
"""Build step: regenerate pack JSON from content-src, then stamp sw.js with
the list of files to precache and a version hash of their contents.

Usage: python3 tools/build.py
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

subprocess.run([sys.executable, str(ROOT / "tools/build_packs.py")], check=True)

files = ["index.html", "manifest.webmanifest"]
files += sorted(str(p.relative_to(ROOT)) for p in (ROOT / "app").iterdir() if p.is_file())
files += sorted(str(p.relative_to(ROOT)) for p in (ROOT / "icons").iterdir() if p.is_file())
index = json.loads((ROOT / "packs/index.json").read_text())
files.append("packs/index.json")
for pid in index["packs"]:
    m = json.loads((ROOT / f"packs/{pid}/pack.json").read_text())
    files += [f"packs/{pid}/pack.json"] + [f"packs/{pid}/{f}" for f in m["files"]]
files += [f"vendor/pyodide/{f}" for f in
          ["pyodide.mjs", "pyodide.asm.mjs", "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json"]]

h = hashlib.sha256()
for f in files:
    h.update(f.encode())
    h.update((ROOT / f).read_bytes())
version = h.hexdigest()[:10]

sw = (ROOT / "sw.js").read_text()
sw = re.sub(r'^const VERSION = .*;$', f'const VERSION = "{version}";', sw, count=1, flags=re.M)
sw = re.sub(r'^const ASSETS = .*;$', "const ASSETS = " + json.dumps(["./" + f for f in files]) + ";", sw,
            count=1, flags=re.M)
(ROOT / "sw.js").write_text(sw)
total = sum((ROOT / f).stat().st_size for f in files)
print(f"sw.js: version {version}, {len(files)} files, {total / 1e6:.1f} MB precached")
