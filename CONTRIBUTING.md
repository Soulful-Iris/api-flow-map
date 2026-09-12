# Contributing

## Layout

```
.claude-plugin/marketplace.json                 marketplace catalog (Claude Code)
plugins/api-flow-map/.claude-plugin/plugin.json plugin manifest — bump `version` on every release
plugins/api-flow-map/skills/api-flow-map/       the skill: SKILL.md, scripts/, references/, evals/
tools/validate.py                               manifests + frontmatter + tests
tools/build_skill_zip.py                        builds the claude.ai upload archive into dist/
```

## Working on the scanner

```
cd plugins/api-flow-map/skills/api-flow-map/scripts
python3 -m unittest discover -s tests -t .           # 23 tests: fixtures, labeler, git diff scenario
python3 apiflow.py scan tests/fixtures/spring-orders -o /tmp/out && open /tmp/out/flow-map.html
```

Add a fixture under `scripts/tests/fixtures/<framework>-<domain>/` when you add framework
support, and assert on endpoint ids, properties and a few step labels in `test_scan_fixtures.py`.
Step ids are structural: a change that alters them for unchanged code is a regression.

Heuristics live in `apiflow/tracer.py` (classification) and `apiflow/labeler.py` (wording);
prefer adding a pattern to `IO_PATTERNS` / `NOISE_METHODS` over special-casing a project.

## Before you open a PR

1. `python3 tools/validate.py` passes.
2. `SKILL.md` still describes what the scripts do (the description is what makes Claude pick the skill).
3. If you changed output formats, update `references/model-schema.md` and the CHANGELOG.

## Releasing

See PUBLISHING.md.
