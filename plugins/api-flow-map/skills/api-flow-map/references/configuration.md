# .apiflow.json

Optional, at the repository root (`.apiflow.json`, `apiflow.json`, `.apiflow.yaml`). Every key
is optional; CLI flags override the file.

| key | default | meaning |
|---|---|---|
| `include` | `[]` (everything) | globs relative to the repo root to scan, e.g. `["services/orders/**", "openapi/**"]` |
| `exclude` | `[]` | globs to skip in addition to `.gitignore`, `node_modules`, `build`, `dist`, `vendor`, `.git`… |
| `include_tests` | `false` | scan `test`/`tests`/`__tests__`/`*_test.go`/`*.spec.ts` too |
| `max_file_kb` | `768` | larger files are skipped (generated code, bundles) |
| `max_files` | `20000` | safety cap |
| `max_depth` | `4` | how many internal call levels to expand under a handler |
| `max_steps_per_endpoint` | `400` | budget per endpoint; the flow notes when it is truncated |
| `base_branch` | auto | default base for `diff` (`origin/HEAD` → `main` → `master` → `develop`) |
| `io_patterns` | built-in | extra regexes per kind: `{"io.db": [...], "io.http": [...], "io.queue": [...], "io.cache": [...], "io.file": [...]}` |
| `noise_patterns` | `[]` | regexes for calls to drop from flows (metrics helpers, tracing) |
| `auth_patterns` | `[]` | regexes for calls/conditions that are authorization checks |
| `validation_patterns` | `[]` | regexes for validation helpers |
| `feature_flag_patterns` | `[]` | regexes for feature-flag lookups |
| `hide_kinds` | `["log"]` | kinds hidden by default in the HTML |
| `redact` | `true` | mask secrets in code snippets |
| `snippets` | `true` | include short code snippets (`--no-snippets` to omit) |
| `endpoint_titles` | `{}` | `{"POST /api/v1/orders": "Place an order"}` overrides |

Example:

```json
{
  "include": ["src/main/**", "openapi.yaml"],
  "base_branch": "origin/develop",
  "max_depth": 5,
  "noise_patterns": ["\\bMetrics\\.", "\\bTracer\\."],
  "io_patterns": {"io.http": ["\\bPartnerGateway\\b"]},
  "endpoint_titles": {"GET /api/v1/orders": "List a customer's orders"}
}
```
