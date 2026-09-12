> Original handoff document from the project zip, 2026-09-11, kept verbatim
> below. It describes the effort that produced this repository, including an
> honest status section and a prioritised next-steps list. Where it refers to
> `api-flow-map-marketplace/`, that folder **is** this repository root.

---

# api-flow-map — project handoff (v1.0.0, 2026-09-11)

Everything built in this effort is in this folder. Start with this file, then
`api-flow-map-marketplace/README.md` and `PUBLISHING.md`.

```
api-flow-map-handoff/
├── README.md                        ← this file: goal, what exists, status, next steps
├── api-flow-map-marketplace/        ← THE CODEBASE. Push this folder as a git repo.
│   ├── .claude-plugin/marketplace.json
│   ├── plugins/api-flow-map/        ← the Claude Code plugin (manifest + the skill)
│   │   └── skills/api-flow-map/     ← the skill: SKILL.md, scripts/, references/, evals/
│   ├── tools/                       ← validate.py, build_skill_zip.py, demo.sh
│   ├── .github/                     ← CI + release workflows, CODEOWNERS
│   └── README / PUBLISHING / SECURITY / CONTRIBUTING / CHANGELOG / LICENSE
├── dist/                            ← ready-to-upload skill archives (built from the codebase)
│   ├── api-flow-map-1.0.0.skill     ← claude.ai / Claude Desktop / Skills API
│   └── api-flow-map-1.0.0.zip       ← same bytes, .zip extension for upload dialogs
├── samples/                         ← real output of the tool on the demo PR
│   ├── sample-pr-review.html        ← open this: before/after diagrams, Whole PR, Code changes
│   ├── sample-flow-map.html         ← scan of a repo (no diff)
│   └── sample-pr-comment.md         ← the Markdown that goes on the PR (Mermaid inside)
└── screenshots/                     ← what the views look like
```

---

## 1. What we want

A **corporate, production-ready Claude skill** that gives real software-engineering review
value on API changes:

1. Read an API repository and show each endpoint's request flow as **titles an engineer
   understands** ("Reserve stock with inventory-service", "If score > 60 → hold for review",
   "Respond 201 Created with order DTO"), not code.
2. Detect what a **branch / PR changes** versus the base branch and show it so that one can
   **tell what changed in a whole API PR from a single view** — including changed conditions,
   status codes, auth, new outbound calls, feature flags.
3. Show it as an **easy-to-read box diagram**, with the **important variables** in each box, and
   the old vs. new values when a box is part of the change.
4. **Side-by-side before/after diagrams** across the **whole PR**, plus a familiar,
   **VS Code-style "code changes"** toggle (line numbers, red/green, word-level highlights,
   inline or side by side).
5. Packaged as a **Claude skill** that people use by talking to Claude, distributable through a
   **Claude Code plugin marketplace** (internal GitHub) and as an upload for claude.ai.

## 2. What exists (all working, all in `api-flow-map-marketplace/`)

**Skill** (`plugins/api-flow-map/skills/api-flow-map/`)
- `SKILL.md` — when Claude uses it, the review workflow (diff → explain → annotate → render),
  how to read risk, limits, troubleshooting. Description is written to trigger on "review this
  PR / what does this API do / what changed / CI gate / spec drift".
- `scripts/apiflow.py` — CLI: `scan`, `diff --base`, `explain`, `render --annotations`, `doctor`.
  Exit codes 0/1/2/3/4 (`--fail-on-risk` gate). Python 3.9+ stdlib only; PyYAML optional.
- `scripts/apiflow/` — discovery (git-aware, test exclusion, `.apiflow.json` config), lexer +
  statement parser (Java/Kotlin/C#/JS/TS/Go) and real `ast` for Python, framework extractors
  (Spring MVC/WebFlux, JAX-RS, Express/Koa/Fastify/Hono, NestJS, Next.js, Flask, FastAPI,
  Django REST, Go net/http/gin/echo/chi/gorilla, ASP.NET Core, OpenAPI, serverless.yml/SAM),
  the tracer (call resolution, IO classification, outcomes, feature flags, noise suppression),
  the labeler (plain-English titles and conditions), the differ (structural step matching,
  property diffs, risk scoring, merged before/after flow), git snapshotting via `git archive`
  + merge-base, source diff collection (`codediff.py`), HTML/Markdown/Mermaid renderers,
  annotations merge, secret redaction.
- `scripts/tests/` — 23 tests: four fixture repos (Spring, Express, FastAPI, Go), labeler cases,
  a git-backed diff scenario, code-diff parsing. `python3 -m unittest discover -s tests -t .`
- `references/` — JSON schema, framework coverage/limits, CI integration (GitHub Actions,
  Jenkins), configuration keys, how to write titles/digests.
- `evals/evals.json` — three prompts for the skill-creator test loop.

**HTML review (`flow-diff.html`)**
- Left rail of changed endpoints (method chips, risk dots), "What changed" digest, per-endpoint
  change list with breadcrumbs, property chips with before→after.
- Views: **Before / after diagrams** (default; base left, head right, aligned step by step,
  dashed placeholders, differing values highlighted, untouched steps dimmed), **Merged diagram**
  (one diagram with +/−/~), **Ledger** (compact list). **Whole PR** puts every changed endpoint
  on one page. **Focus on changes** collapses untouched internal calls. **⟨/⟩ Code changes** =
  IDE-style diff under changed boxes + full file diffs (inline / side by side).
- Self-contained: no CDN, no fonts, works offline, prints.

**Markdown (`flow-diff.md`)** — PR-comment digest table + per-endpoint `<details>` with the
change list, a `diff`-fenced flow and a Mermaid flowchart (variables in nodes, diff colouring;
validated against Mermaid's parser).

**Repository plumbing** — marketplace + plugin manifests, `tools/validate.py` (manifests,
frontmatter, tests), `tools/build_skill_zip.py`, `tools/demo.sh` (builds a demo repo + branch,
runs the diff, opens the review), CI workflow (Python 3.9 + 3.12), release workflow (tag →
archives on a GitHub Release), CODEOWNERS, SECURITY.md, PUBLISHING.md, MIT LICENSE.

## 3. Status — honest assessment

Verified end to end: Spring, Express, FastAPI and Go fixtures; a real project (spring-petclinic,
14 endpoints, clean output after two fixes); the git diff scenario; every generated Mermaid
diagram; HTML in headless Chromium (no JS errors); plugin runs from a copied directory (what
Claude Code does on install).

Smoke-tested only (code written, no fixture): NestJS, Next.js, Django REST/urls.py,
flask-restful, ASP.NET Core (attribute routing + minimal APIs), serverless.yml/SAM, OpenAPI
YAML. Expect rough edges there.

Known limits (also in SKILL.md and references/frameworks.md): static heuristic tracing — no
reflection, dynamic dispatch, DI-by-name, global filters/interceptors registered elsewhere,
generated code; 4 call levels / 400 steps per endpoint by default; conditions humanised by
rules; Ruby/PHP/Scala/Rust not covered; GraphQL/gRPC not covered.

## 4. How it is used (inside Claude)

Install once, then talk to Claude — you never run the scripts yourself:

- **Claude Code** (recommended; it sits in the repo with git access):
  `/plugin marketplace add <owner>/<repo>` → `/plugin install api-flow-map@bruno-api-tools`,
  then: *"Review what this branch changes in the API compared to origin/main."*
  Claude runs `diff`, reads the JSON, writes the digest/titles, re-renders, and hands you
  `apiflow-out/flow-diff.html` + `flow-diff.md`. Also: *"Map every endpoint in this repo and
  explain what each does"*, *"Set up a CI gate that blocks PRs changing auth or status codes."*
- **Claude Desktop / Cowork**: same, when Claude has access to the repo folder.
- **claude.ai (browser)**: upload `dist/api-flow-map-1.0.0.zip` under Customize > Skills. The
  sandbox has no network/git access, so only `scan` on an uploaded source zip is practical there.

To try without Claude: `cd api-flow-map-marketplace && python3 tools/validate.py && tools/demo.sh`.

## 5. What should be done next (priority order)

**A. Prove it on real code (highest value, do first)**
1. Run `doctor` then `diff --base origin/main` on 3–5 real internal API repos (Spring first).
2. Collect the `diagnostics` from `flow-diff.json`, endpoints flagged `unresolved` /
   `interface-only` / "handler could not be located", and any titles that read badly.
3. Fix by adding patterns (`IO_PATTERNS`, `NOISE_METHODS`, `AUTH_RX`… in `tracer.py`; wording
   in `labeler.py`) and add a fixture + test per pattern class. Corporate conventions (custom
   base controllers, internal HTTP client wrappers, entitlement checks, feature-flag SDK) are
   the likely gaps; `.apiflow.json` can carry repo-specific patterns without code changes.

**B. Publish**
4. Create the internal repo from `api-flow-map-marketplace/`; set marketplace `name`/`owner`,
   CODEOWNERS, license decision (MIT placeholder; proprietary is fine internally).
5. Security review with SECURITY.md (no network, read-only git, redaction, outputs contain
   source excerpts — `--no-snippets --no-code-diff` for a sanitized variant).
6. Tag `v1.0.0` → release workflow → archives. Announce install commands; optionally sync
   through Organization settings > Plugins so the team gets it automatically.

**C. Product polish (backlog)**
7. NestJS: default 201 for POST; Django REST: simplify the ViewSet `@action` path code
   (`python_web.py`, marked in the source); fixtures + tests for NestJS, DRF, ASP.NET, serverless.
8. Global auth detection: Spring `SecurityFilterChain` / `OncePerRequestFilter`, NestJS
   `APP_GUARD`, Express `app.use(auth)` in other entry files — today these only count when
   they sit on the route's mount path.
9. Whole-PR page: keyboard navigation between endpoints; export a diagram as SVG/PNG; dark mode.
10. PR comment: respect GitHub's 65k-character comment limit (truncate flows, link to the
    artifact); reusable GitHub Action wrapper; Jenkins shared library step.
11. Run the skill-creator eval loop (`evals/evals.json`) with Claude to tune the SKILL.md
    description/triggering after the first real-repo runs.
12. Kotlin coroutine flows and Java records/sealed types deserve a fixture; C# `record` DTOs too.

## 6. Design decisions worth keeping

- **Deterministic scripts, Claude writes the words.** The scanner/differ never call a model, so
  CI results are stable and diffs are reproducible; Claude improves titles and writes the digest
  through an annotations file merged at render time (`explain` → annotations → `render`).
- **Structural step ids** (kind + target + condition + position, never line numbers) so
  reformatting, comments and moved blocks are not "changes".
- **Base = merge-base(base, head)**, head = working tree (uncommitted included) unless `--head`.
- **Read-only, offline.** Snapshots via `git archive`; no writes to the checkout; no network.
- **Risk is triage, not a verdict**: high = removed endpoint, route/method, auth/validation,
  success status, removed DB write, params/body; medium = new/removed IO, new gates, new error
  status, feature flags, new endpoint; low = the rest.
