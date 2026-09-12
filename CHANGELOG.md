# Changelog

## 1.0.1 - 2026-09-12

- Document that Python source is parsed with the running interpreter: on 3.9 a
  repo using `match` or newer syntax has those files skipped, reported in
  `diagnostics` and `doctor`. Check `doctor` when a Python flow looks short.
- Test suite asserts the version-appropriate result on 3.9 and 3.12, and
  asserts the skipped-file diagnostic rather than hiding the case.
- `tools/pre-push` + `tools/install-hook.sh`: deterministic pre-push gate that
  refuses a push when API risk reaches `high`. No model call.

## 1.0.0 — 2026-09-11

Initial release.

- Endpoint discovery for Spring MVC/WebFlux, JAX-RS, Express/Koa/Fastify/Hono, NestJS, Next.js,
  Flask, FastAPI, Django REST, Go net/http/gin/echo/chi/gorilla, ASP.NET Core, OpenAPI specs,
  serverless.yml/SAM.
- Flow tracing into plain-English steps (validation, auth, DB, HTTP, queues, cache, files,
  conditions, loops, error handling, responses, failures) with structural step ids.
- Branch/PR diff with property changes, flow changes, risk scoring, `--fail-on-risk` CI gate.
- Self-contained HTML review: before/after box diagrams aligned step by step, merged diagram,
  ledger, whole-PR page, IDE-style code changes (inline / side by side), search, print.
- Markdown PR comment with Mermaid flowcharts; JSON models; annotations merge for Claude-written
  titles and digests.
