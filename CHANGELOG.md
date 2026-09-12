# Changelog

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
