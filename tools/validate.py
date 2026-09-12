#!/usr/bin/env python3
"""Repository health check (no Claude Code CLI required).

Checks the marketplace catalog, the plugin manifest and the skill frontmatter,
then runs the skill's unit tests. Exit code 0 = ready to publish.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESERVED = {"claude-code-marketplace", "claude-code-plugins", "claude-plugins-official", "claude-plugins-community", "claude-community",
            "anthropic-marketplace", "anthropic-plugins", "agent-skills", "anthropic-agent-skills", "knowledge-work-plugins", "life-sciences",
            "claude-for-legal", "claude-for-financial-services", "financial-services-plugins", "first-party-plugins", "claude-tag-plugins", "healthcare"}
KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
problems: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        problems.append(msg)


def main() -> int:
    mp_path = os.path.join(ROOT, ".claude-plugin", "marketplace.json")
    check(os.path.isfile(mp_path), "missing .claude-plugin/marketplace.json")
    if os.path.isfile(mp_path):
        mp = json.load(open(mp_path, encoding="utf-8"))
        for key in ("name", "owner", "plugins"):
            check(key in mp, f"marketplace.json: missing required field '{key}'")
        name = mp.get("name", "")
        check(bool(KEBAB.match(name)), f"marketplace name '{name}' must be kebab-case")
        check(name not in RESERVED and not re.search(r"anthropic|official", name), f"marketplace name '{name}' is reserved or impersonates Anthropic")
        check(bool((mp.get("owner") or {}).get("name")), "marketplace.json: owner.name is required")
        names = [p.get("name") for p in mp.get("plugins", [])]
        check(len(names) == len(set(names)), "duplicate plugin names in marketplace.json")
        for p in mp.get("plugins", []):
            check(bool(KEBAB.match(p.get("name", ""))), f"plugin name '{p.get('name')}' must be kebab-case")
            src = p.get("source")
            check(isinstance(src, (str, dict)), f"plugin '{p.get('name')}': source is required")
            if isinstance(src, str):
                check(src.startswith("./") and ".." not in src, f"plugin '{p.get('name')}': relative source must start with ./ and stay inside the repo")
                pdir = os.path.join(ROOT, src)
                check(os.path.isdir(pdir), f"plugin '{p.get('name')}': source directory {src} not found")
                pj = os.path.join(pdir, ".claude-plugin", "plugin.json")
                check(os.path.isfile(pj), f"plugin '{p.get('name')}': missing {src}/.claude-plugin/plugin.json")
                if os.path.isfile(pj):
                    pjd = json.load(open(pj, encoding="utf-8"))
                    check(pjd.get("name") == p.get("name"), f"plugin.json name '{pjd.get('name')}' differs from marketplace entry '{p.get('name')}'")
                    if "version" in p and "version" in pjd:
                        check(p["version"] == pjd["version"], f"plugin '{p.get('name')}': version differs between marketplace.json ({p['version']}) and plugin.json ({pjd['version']})")
                check(not os.path.isdir(os.path.join(pdir, "bin")), f"plugin '{p.get('name')}': a top-level bin/ directory is rejected by claude.ai org distribution; use scripts/")
                skills_dir = os.path.join(pdir, "skills")
                check(os.path.isdir(skills_dir), f"plugin '{p.get('name')}': no skills/ directory")
                if os.path.isdir(skills_dir):
                    for sk in sorted(os.listdir(skills_dir)):
                        skill_md = os.path.join(skills_dir, sk, "SKILL.md")
                        check(os.path.isfile(skill_md), f"skill '{sk}': missing SKILL.md")
                        if os.path.isfile(skill_md):
                            check_skill(skill_md, sk)
    # unit tests of the skill
    tests_dir = os.path.join(ROOT, "plugins", "api-flow-map", "skills", "api-flow-map", "scripts")
    if os.path.isdir(os.path.join(tests_dir, "tests")):
        r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."], cwd=tests_dir, capture_output=True, text=True)
        check(r.returncode == 0, "unit tests failed:\n" + (r.stderr or r.stdout)[-2000:])
        tail = (r.stderr or r.stdout).strip().split("\n")[-1]
        print(f"tests: {tail}")
    if problems:
        print("PROBLEMS:")
        for p in problems:
            print(" -", p)
        return 1
    print("ok: marketplace, plugin manifest, skill frontmatter and tests are valid")
    return 0


def check_skill(path: str, sk: str) -> None:
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    check(bool(m), f"skill '{sk}': SKILL.md must start with YAML frontmatter")
    if not m:
        return
    fm = m.group(1)
    name = re.search(r"^name:\s*(.+)$", fm, re.M)
    desc = re.search(r"^description:\s*(.+)$", fm, re.M)
    check(bool(name), f"skill '{sk}': frontmatter needs 'name'")
    check(bool(desc), f"skill '{sk}': frontmatter needs 'description'")
    if name:
        check(name.group(1).strip() == sk, f"skill '{sk}': frontmatter name '{name.group(1).strip()}' must match the folder name")
        check(bool(KEBAB.match(name.group(1).strip())) and len(name.group(1).strip()) <= 64, f"skill '{sk}': name must be kebab-case, max 64 chars")
    if desc:
        d = desc.group(1).strip()
        check(len(d) <= 1024, f"skill '{sk}': description must be at most 1024 characters (has {len(d)})")
        check("<" not in d and ">" not in d, f"skill '{sk}': description must not contain angle brackets")
    unknown = [k for k in re.findall(r"^([A-Za-z_-]+):", fm, re.M) if k not in ("name", "description", "license", "allowed-tools", "metadata", "compatibility")]
    check(not unknown, f"skill '{sk}': unexpected frontmatter keys {unknown}")


if __name__ == "__main__":
    sys.exit(main())
