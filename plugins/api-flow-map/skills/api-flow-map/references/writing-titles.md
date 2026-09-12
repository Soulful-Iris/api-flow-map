# Writing titles, summaries and the digest

The scripts produce deterministic *auto* titles. They are fine for CI and for stable diffs,
but a human reader deserves better wording in the places they will actually read. Annotations
let Claude improve the text without touching the model (auto titles are kept alongside).

## Annotation file

```json
{
  "digest": "Fraud review now triggers at score > 60 (was 80), so more orders will be held. Order confirmation emails go out behind the `order-confirmation-email` flag. **Breaking:** `POST /api/v1/orders/{id}/cancel` now returns 200 instead of 204, and `GET /api/v1/orders/{id}` now requires ORDER_ADMIN.",
  "endpoints": {
    "POST /api/v1/orders": {
      "title": "Place an order",
      "summary": "Validates the request, reserves stock, charges the card and publishes ORDER_PLACED. Orders over the review threshold are fraud-scored and may be held.",
      "changes_summary": "Lower fraud threshold (60) and a new, flag-gated confirmation email after the order is saved.",
      "steps": {
        "29f04e5db8": "Score the order with the fraud service",
        "d41b1fff79": "If the fraud score is above 60, hold the order for review"
      }
    }
  }
}
```

- `digest` — 2 to 4 sentences. Lead with the change a client or on-call engineer would care
  about most. Say *what* changed and *why it matters*, not how the tool found it. Markdown-lite:
  `**bold**` and `` `code` `` only.
- `changes_summary` — one or two sentences per changed endpoint.
- `title` / `summary` — for endpoints people will read in a document. Titles are verbs first
  ("Place an order", "Cancel an order"), ≤ 6 words. Summaries describe the happy path and the
  main failure modes in one or two sentences.
- `steps` — keyed by the step id printed by `explain`. Keep step titles ≤ 8 words, one action
  each, present tense, imperative: "Reserve stock with inventory-service", "Fail with 409 when
  stock is missing", "If order total is above the review threshold". Prefer domain words over
  code words (order, customer, reservation) but keep service names and status codes exact.

## Rules

1. Only describe what the model or the source shows. If a step is `external`, `unresolved` or
   `interface-only`, say "likely" or leave the auto title.
2. In diff mode, annotate the changed endpoints first; unchanged endpoints only if asked.
3. Keep status codes, HTTP verbs, paths, topic names and feature-flag names verbatim.
4. Do not rewrite a condition into its opposite. `If stock is not available` stays negative.
5. Unknown step ids are ignored, so annotations from a previous run do not break a re-render;
   still re-run `explain` after code changes because ids follow structure.

## Where the auto titles come from

- Endpoint: config override → OpenAPI summary → handler method name → verb + resource from
  the route (`GET /orders/{id}` → "Get order by ID", `POST /orders/{id}/cancel` → "Cancel order").
- Repository calls: Spring Data / ORM verbs (`findByCustomerId` → "Query orders by customer ID").
- HTTP clients: Feign/HttpExchange verb + path, URL literals, template/f-string variables
  (`${PAYMENTS_URL}/v2/charges` → "Call payments service: POST /v2/charges").
- Queues: topic literal or constant, event type from `new OrderPlacedEvent(...)` or `type: '...'`.
- Conditions: null/empty idioms, negations, `compareTo`, `errors.Is`, feature-flag helpers.
- Exits: `ResponseEntity.status(...)`, `res.status(404).json(...)`, `raise HTTPException(...)`,
  `http.Error(w, …, 404)`, `NotFound()` and friends.
