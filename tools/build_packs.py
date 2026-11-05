#!/usr/bin/env python3
"""Build packs/<pack>/<file>.json from content-src/<pack>/<file>.py.

Each content-src module defines ITEMS = [...] (list of dicts matching
schema/pack.schema.json). The output file name is the module name.

Usage: python3 tools/build_packs.py [pack-id ...]
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "content-src"
sys.path.insert(0, str(SRC))


def build(pack_dir: Path):
    out_dir = ROOT / "packs" / pack_dir.name
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((out_dir / "pack.json").read_text())
    for mod_path in sorted(pack_dir.glob("*.py")):
        if mod_path.name.startswith("_"):
            continue
        spec = importlib.util.spec_from_file_location(f"{pack_dir.name}.{mod_path.stem}", mod_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        doc = {"version": manifest["version"], "items": mod.ITEMS}
        name = mod_path.stem.replace("_", "-") + ".json"
        (out_dir / name).write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
        print(f"  {pack_dir.name}/{name}: {len(mod.ITEMS)} items")


if __name__ == "__main__":
    wanted = set(sys.argv[1:])
    for d in sorted(p for p in SRC.iterdir() if p.is_dir() and not p.name.startswith("_")):
        if not wanted or d.name in wanted:
            build(d)
