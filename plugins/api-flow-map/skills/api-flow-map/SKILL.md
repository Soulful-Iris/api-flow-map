---
name: api-flow-map
description: Map API request flows and review what a branch or PR changes. Scans API repositories (Spring MVC/WebFlux, JAX-RS, Express/Koa/Fastify/NestJS/Next.js, Flask/FastAPI/Django REST, Go net-http/gin/echo/chi/gorilla, ASP.NET Core, OpenAPI specs, serverless.yml/SAM) and produces per-endpoint flows in plain English (validation, auth, DB reads/writes, outbound HTTP, queue publishes, conditions, status codes), then diffs them against a base branch with risk scoring and a self-contained HTML review view plus a Markdown PR comment. Use whenever someone asks what an API does, wants endpoint documentation or a flow diagram, needs to review an API pull request or branch, asks what changed in an API between branches or commits, wants a CI gate for risky API changes, or wants to check OpenAPI spec vs implementation drift.
---

# api-flow-map

Turns an API codebase into endpoint flows a reviewer can read in a minute, and turns a branch
into a change review: which endpoints changed, what steps were added/removed/modified, which
conditions or status codes moved, and how risky that is. Deterministic Python (stdlib only,
PyYAML optional), no network, no build required, read-only on the repo.

## Quick start

The tooling is bundled with this skill: `scripts/apiflow.py` sits next to this SKILL.md
(in a Claude Code plugin install that is `${CLAUDE_PLUGIN_ROOT}/skills/api-flow-map/scripts`).

```bash
S=<directory containing this SKILL.md>/scripts
python3 $S/apiflow.py doctor <repo>                                  # what will be detected
python3 $S/apiflow.py scan   <repo> -o <out>                         # flow-map.html / .md / .json
python3 $S/apiflow.py diff   <repo> --base origin/main -o <out>      # flow-diff.html / .md / .json (PR review)
python3 $S/apiflow.py explain <out>/flow-diff.json --changed-only    # outline with step ids, for annotations
python3 $S/apiflow.py render  <out>/flow-diff.json --annotations ann.json -o <out>
```

Write outputs under the user's workspace (e.g. `apiflow-out/` inside the repo, or the outputs
folder); the HTML is a single file with no external assets — attach it to the PR or open it locally.

## Workflow A — review a PR / branch (primary use)

1. **Diff.** Run `apiflow.py diff <repo> --base <base>`. The base defaults to `origin/HEAD`,
   then `main`/`master`/`develop`. Head is the working tree (uncommitted changes included); pass
   `--head <ref>` to compare committed refs. The base is taken at `merge-base(base, head)`, so
   unrelated commits on the base branch do not pollute the review. Read the console summary.
2. **Understand the changes.** `apiflow.py explain <out>/flow-diff.json --changed-only` prints,
   per changed endpoint, the property changes (auth, validation, params, body, status codes),
   the flow changes with breadcrumbs, and the merged flow with `+`/`-`/`~` markers and step ids.
   Open `flow-diff.json` for full detail (schema: `references/model-schema.md`). Look at the
   actual source for anything marked `unresolved`, `depth-limit` or with a warning before
   asserting behaviour.
3. **Annotate.** Write an annotations JSON (`references/writing-titles.md`): a two-to-four
   sentence `digest` a reviewer should read first (lead with the highest-risk change and say
   why it matters to clients), a `changes_summary` per changed endpoint, and better `title`s
   for steps whose auto title is awkward — only for changed endpoints unless asked. Never
   describe behaviour that is not in the model or the code.
4. **Render and deliver.** `apiflow.py render <out>/flow-diff.json --annotations ann.json -o <out>`
   rewrites `flow-diff.html` and `flow-diff.md`. Point the user at the HTML: left rail = changed
   endpoints, top = what changed, main pane = **before / after box diagrams** (base branch on the
   left, this branch on the right, aligned step by step: one box per step with the variables and
   arguments involved, conditions with yes/no arms, responses as pills; added boxes only on the
   right, removed only on the left with a dashed placeholder opposite, modified boxes on both
   sides with the differing values highlighted; untouched steps dimmed). `Whole PR` puts every
   changed endpoint on one page this way, for review or printing. Other views: `Merged diagram`
   (one diagram with +/−/~ colouring), `Ledger` (compact list); `Focus on changes` collapses
   untouched internal calls; `⟨/⟩ Code changes` adds the IDE-style source diff (changed lines
   under each changed box plus full file diffs, inline or side by side, with line numbers and
   word-level highlights). Offer `flow-diff.md` as the PR comment (it embeds a Mermaid flowchart per changed
   endpoint with the same colouring, so it renders on GitHub/GitLab). In the chat reply, give
   the risk level, the top three findings with file:line, and anything the scanner could not
   resolve.

The `diff` exit code is 4 when `--fail-on-risk <level>` is reached, which is how CI gates work
(`references/ci-integration.md`). `diff` embeds the git diff of the files the changed endpoints
touch (`file_diffs` in the JSON) so the HTML can show source; `--no-code-diff` skips that for a
smaller artifact.

## Workflow B — map an API repository

1. `apiflow.py doctor <repo>` — confirms frameworks, endpoint count, handlers it cannot locate.
   If nothing is found, check `references/frameworks.md` and the `include` config.
2. `apiflow.py scan <repo> -o <out>` — `flow-map.html` (browse endpoints; `Box diagram` /
   `Ledger` views; `Code` toggle shows the underlying calls; `All endpoints` + print for a
   shareable document), `flow-map.md` (tables, indented flows and a Mermaid flowchart per
   endpoint with the variables in each box), `flow-map.json`.
3. Optional but recommended for documents people will read: `explain flow-map.json`, write
   annotations (endpoint titles/summaries, step titles), `render --annotations`.

## Reading the output

- **Step kinds**: `call` (internal, expandable), `io.db`, `io.http`, `io.queue`, `io.cache`,
  `io.file`, `branch` (if/switch with arms; `exits` marks arms that return/throw), `loop`,
  `try` (arms: Try / On X / Finally), `return` (status code chip), `throw` (mapped to a status
  when the exception is known: `@ResponseStatus`, `@ControllerAdvice`, NestJS/FastAPI/Django
  exceptions, `HttpException(…, 404)`), `validate`, `auth`, `transform`, `external`
  (unresolved collaborator, dashed), `log` (hidden by default).
- **Endpoint properties**: auth, validation, body, path/query/header params, declared and
  observed status codes, response type, feature flags, documented (OpenAPI reconciliation:
  spec-only endpoints get a warning, undocumented ones `documented: no`).
- **Diff semantics**: steps are matched structurally (kind + target + condition + outcome), not
  by text or line, so reformatting, renames of descriptions and moved blocks are not changes.
  `modified` = same step with a different condition, outcome or target (the old value is shown
  as "was"). `moved` = same step at a different position. Endpoint status: added / removed /
  modified / unchanged; a route change on the same handler is reported as a modification with
  a high-risk "Route changed" note.
- **Risk**: high = removed endpoint, route/method change, auth or validation removed or
  changed, success status code changed, removed DB write, params/body changed; medium = new
  or removed outbound IO, new condition around IO or exits, new error status, feature-flag
  gating, new endpoint; low = everything else. Risk is a triage aid, not a verdict.

## Limits (say them when relevant)

Static, heuristic tracing, not a compiler: dynamic dispatch, reflection, DI resolved by name at
runtime, interceptors/filters/decorators registered elsewhere, generated code and macros are
either invisible or shown as `external`/`interface-only`. Calls are followed at most
`max_depth` (4) levels and 400 steps per endpoint (configurable). Conditions are humanised
heuristically; the code snippet is one toggle away. Secrets in snippets are redacted. Treat the
map as an accurate index of *where to look*, and verify anything surprising in the source.

**Python source is parsed with the interpreter you are running.** `ast` only understands syntax
its own version knows, so running apiflow on Python 3.9 against a repo that uses `match`
statements (3.10) or newer syntax will skip those files. They are not dropped silently: each one
appears in `diagnostics` and in `doctor` as `python syntax error at line N; file skipped`, and
any flow that would have been traced through them is simply absent. If `doctor` reports syntax
errors on code you know is valid, run apiflow on a newer interpreter.

## Configuration

`.apiflow.json` at the repo root (all optional): `include`/`exclude` globs, `include_tests`,
`max_depth`, `max_steps_per_endpoint`, `max_file_kb`, `base_branch`, `io_patterns`,
`noise_patterns`, `auth_patterns`, `validation_patterns`, `feature_flag_patterns`,
`hide_kinds`, `redact`, `snippets`, `endpoint_titles`. Details and examples in
`references/configuration.md`. CLI flags `--include/--exclude/--include-tests/--max-depth`
override the file.

## Troubleshooting

- *No endpoints found* → `doctor`; check the API lives under an included path and the
  framework is covered; for monorepos pass `--include "services/orders/**"`.
- *YAML spec or serverless.yml skipped* → `pip install pyyaml` (JSON specs work without it).
- *Handler could not be located* → shown as a warning on the endpoint; the route is still listed.
- *diff says "not a git repository"* → `diff` needs git history; `scan` works on plain folders.
- *Too much noise from a helper* → add it to `noise_patterns`; *a client not recognised as
  HTTP/queue* → add to `io_patterns`.

## Tests

`cd scripts && python3 -m unittest discover -s tests -t .` runs the fixture scans (Spring,
Express, FastAPI, Go), labeler cases and a git-backed diff scenario.
