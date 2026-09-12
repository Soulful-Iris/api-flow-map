# JSON outputs

Both files are plain JSON, stable across runs on the same tree (ids are structural, never
line-based), and safe to diff or store as CI artifacts.

## flow-map.json (scan)

```
{
  "schema_version": "1.0",
  "generated_at": "2026-09-11T03:53:00+00:00",
  "repo": {"root": "...", "name": "orders-api", "git": {"branch": "...", "commit": "abc1234", "dirty": false, "subject": "..."}},
  "frameworks": ["spring", "feign", "spring-data"],
  "stats": {"files_scanned": 17, "functions_indexed": 52, "endpoints": 5, "steps": 41, "untraced_endpoints": 0, "duration_ms": 55},
  "diagnostics": ["..."],                    // files skipped, parse problems, missing PyYAML
  "endpoints": [ Endpoint ]
}

Endpoint = {
  "id": "POST /api/v1/orders",              // METHOD + normalised path ({id} placeholders)
  "method": "POST", "path": "/api/v1/orders",
  "title": "Place a new order", "auto_title": "...", "summary": "",
  "handler": {"name": "OrderController.createOrder", "file": "src/.../OrderController.java", "line": 37, "lang": "java"},
  "framework": "spring", "source": "code" | "openapi" | "serverless",
  "properties": {                            // only present when detected
    "auth": ["hasRole('ORDER_WRITE')"], "validation": ["@Valid CreateOrderRequest"], "body": "CreateOrderRequest",
    "path_params": ["id"], "query_params": ["limit?"], "headers": ["X-Request-Id"],
    "status": 201, "responses": [201, 400, 409], "declared_responses": [201, 409], "returns": "OrderDto",
    "documented": true, "spec_summary": "...", "deprecated": false, "feature_flags": ["manual-review"],
    "consumes": [...], "produces": [...], "rate_limit": [...], "cache": [...], "transactional": true, "async": true
  },
  "warnings": ["declared in the OpenAPI spec but no implementation was found in the code"],
  "flow": [ Step ]
}

Step = {
  "id": "85a9d2f8a7",                        // structural id (kind + target + condition + position)
  "kind": "call|io.db|io.http|io.queue|io.cache|io.file|branch|loop|try|return|throw|validate|auth|transform|log|external|note",
  "label": "Call inventory-service: POST /reservations", "auto_label": "...", "summary": "",
  "detail": "InventoryClient.reserve(order.getItems())",   // technical form
  "target": "InventoryClient.reserve",                      // resolved callee when known
  "condition": "",                            // branch/loop
  "outcome": {"status": 409, "throws": "OutOfStockException"},   // return/throw, or io steps with or-fails
  "tags": ["early-exit", "guard", "feature-flag", "flag:manual-review", "wrapper", "unresolved", "recursion", "depth-limit", "interface-only", "or-fails", "has-default", "async", "error-propagation"],
  "location": {"file": "...", "line": 52},
  "code": "inventoryClient.reserve(order.getItems())",      // redacted snippet (optional)
  "children": [ Step ],                        // expanded body of an internal call
  "branches": [ {"label": "If stock is not available", "condition": "!stock.isAvailable()", "exits": true, "steps": [ Step ]} ]
}
```

## flow-diff.json (diff)

```
{
  "schema_version": "1.0", "generated_at": "...",
  "repo": {...}, "frameworks": [...],
  "base": {"ref": "origin/main", "commit": "5d9c6ac", "subject": "..."},
  "head": {"branch": "feature/x", "commit": "981aaf3", "dirty": true},
  "changed_files": ["src/..."],
  "summary": {
    "endpoints_added": 1, "endpoints_removed": 1, "endpoints_modified": 3, "endpoints_unchanged": 0,
    "steps_added": 5, "steps_removed": 2, "steps_modified": 2,
    "risk": "high", "risk_reasons": [{"endpoint": "...", "title": "...", "severity": "high", "reason": "...", "status": "modified"}],
    "changed_endpoints": ["..."]
  },
  "endpoints": [ DiffEndpoint ],
  "diagnostics": {"base": [...], "head": [...]},
  "file_diffs": {                              // git diff of the files the changed endpoints touch (omit with --no-code-diff)
    "files": {"src/.../OrderServiceImpl.java": {"path": "...", "old_path": null, "status": "modified|added|deleted|renamed|binary", "truncated": false,
              "hunks": [{"header": "@@ -53,7 +55,7 @@ ...", "old_start": 53, "new_start": 55,
                         "lines": [{"t": " ", "o": 53, "n": 55, "s": "..."}, {"t": "-", "o": 56, "n": null, "s": "if (score > 80) {", "w": [[24, 25]]}, {"t": "+", "o": null, "n": 58, "s": "if (score > 60) {", "w": [[24, 25]]}]}]}},
    "skipped": ["files over the size budget"]
  }
}

DiffEndpoint = Endpoint fields (from head, or base when removed) plus:
  "status": "added|removed|modified|unchanged", "risk": "none|low|medium|high", "note": "was spec-only" (optional),
  "risk_reasons": [{"severity", "reason"}],
  "property_changes": [{"key": "auth", "label": "Authorization", "before": [...], "after": [...], "severity": "high", "reason": "..."}],
  "flow_changes": [{"type": "added|removed|modified|moved", "kind": "...", "path": ["Place order", "If ..."], "label": "...",
                    "severity": "medium", "reason": "...", "step_id": "...", "location": {...},
                    "before": {...}, "after": {...}, "changed_fields": ["condition"]}],
  "counts": {"added": 1, "removed": 0, "modified": 1},
  "before": {"id": "...", "title": "...", "properties": {...}},
  "flow": [ MergedStep ]

MergedStep = Step fields plus:
  "change": "same|added|removed|modified|moved|moved-from",
  "changed_fields": ["condition" | "outcome" | "target" | "detail" | "tags"],
  "before": {"label", "detail", "condition", "outcome", "code", "location", "target"},   // when modified
  "nested_changes": {"added": 1, "removed": 0, "modified": 1},                            // on ancestors of changes
  "branches": [ {..., "change": "same|added|removed|modified", "before": {"label", "condition"}} ]
```

Annotation files (see writing-titles.md) are merged at render time and never change these files.
