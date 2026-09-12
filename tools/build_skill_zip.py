#!/usr/bin/env python3
"""Build the uploadable skill archive for claude.ai / Claude Desktop / the Skills API.

Produces dist/api-flow-map-<version>.skill and an identical .zip (claude.ai's
upload dialog wants a .zip containing a folder with SKILL.md). The archive is
built from plugins/api-flow-map/skills/api-flow-map so the repository stays the
single source of truth.
"""
from __future__ import annotations

import json
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_DIR = os.path.join(ROOT, "plugins", "api-flow-map", "skills", "api-flow-map")
EXCLUDE_DIRS = {"__pycache__", "evals", ".pytest_cache"}


def main() -> int:
    version = json.load(open(os.path.join(ROOT, "plugins", "api-flow-map", ".claude-plugin", "plugin.json"), encoding="utf-8")).get("version", "0.0.0")
    dist = os.path.join(ROOT, "dist")
    os.makedirs(dist, exist_ok=True)
    out = os.path.join(dist, f"api-flow-map-{version}.skill")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for dirpath, dirnames, filenames in os.walk(SKILL_DIR):
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
            for fn in sorted(filenames):
                if fn.endswith(".pyc"):
                    continue
                full = os.path.join(dirpath, fn)
                arc = os.path.join("api-flow-map", os.path.relpath(full, SKILL_DIR))
                zf.write(full, arc)
    zip_copy = out[:-6] + ".zip"
    with open(out, "rb") as src, open(zip_copy, "wb") as dst:
        dst.write(src.read())
    print(f"built {out}\nbuilt {zip_copy}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
