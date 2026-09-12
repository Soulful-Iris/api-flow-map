import unittest

from .helpers import all_steps, find_ep, fixture, labels
from apiflow.scanner import scan


class SpringFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = scan(fixture("spring-orders"))

    def test_endpoints_discovered_with_prefix_and_spec_reconciliation(self):
        ids = {e.id for e in self.model.endpoints}
        self.assertEqual(ids, {"GET /api/v1/orders", "POST /api/v1/orders", "GET /api/v1/orders/{id}",
                               "POST /api/v1/orders/{id}/cancel", "GET /api/v1/orders/{id}/receipt"})
        receipt = find_ep(self.model, "GET", "/receipt")
        self.assertEqual(receipt.source, "openapi")
        self.assertTrue(any("no implementation" in w for w in receipt.warnings))
        get = find_ep(self.model, "GET", "/orders/{id}")
        self.assertTrue(get.properties["documented"])
        self.assertEqual(get.title, "Fetch a single order")           # spec summary wins
        self.assertFalse(find_ep(self.model, "GET", "/api/v1/orders").properties["documented"])

    def test_properties(self):
        post = find_ep(self.model, "POST", "/api/v1/orders")
        p = post.properties
        self.assertEqual(p["auth"], ["hasRole('ORDER_WRITE')"])
        self.assertEqual(p["status"], 201)
        self.assertEqual(p["body"], "CreateOrderRequest")
        self.assertIn("@Valid CreateOrderRequest", p["validation"])
        self.assertEqual(p["headers"], ["X-Request-Id"])
        self.assertEqual(p["responses"], [201, 400, 409])
        self.assertEqual(p["declared_responses"], [201, 409])

    def test_flow_reads_like_english_and_follows_calls(self):
        post = find_ep(self.model, "POST", "/api/v1/orders")
        ls = labels(post)
        for expected in ("Place order", "Validate request", "Call inventory-service: POST /reservations", "If stock is not available",
                         "Fail: out of stock (409 Conflict)", "Call fraud service: POST /score", "If score > 80", "Save order",
                         "Publish OrderPlacedEvent to 'order-events' via Kafka", "Call payment-service: POST /v2/charges",
                         "Rethrow payment declined", "Respond 201 Created with order DTO"):
            self.assertIn(expected, ls, f"missing step {expected!r} in {ls}")
        kinds = {s.kind for s in all_steps(post.flow)}
        self.assertTrue({"call", "io.http", "io.db", "io.queue", "branch", "try", "throw", "return"} <= kinds)
        # getters/setters/constructors are noise
        self.assertFalse(any(l.startswith(("Get ", "Set ")) for l in ls), ls)

    def test_or_else_throw_and_switch(self):
        cancel = find_ep(self.model, "POST", "/cancel")
        ls = labels(cancel)
        self.assertIn("Load order by ID — or fail: order not found (404 Not Found)", ls)
        self.assertIn("Depending on order status", ls)
        self.assertIn("Respond 204 No Content", ls)
        self.assertEqual(cancel.properties["responses"], [204, 404])

    def test_step_ids_are_stable_across_rescans(self):
        again = scan(fixture("spring-orders"))
        a = [s.id for e in self.model.endpoints for s in all_steps(e.flow)]
        b = [s.id for e in again.endpoints for s in all_steps(e.flow)]
        self.assertEqual(a, b)
        self.assertEqual(len(set(a)), len(a), "step ids must be unique")


class ExpressFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = scan(fixture("express-orders"))

    def test_mounts_middleware_and_inline_handlers(self):
        ids = {e.id for e in self.model.endpoints}
        self.assertEqual(ids, {"GET /health", "GET /api/v1/orders/{id}", "POST /api/v1/orders", "DELETE /api/v1/orders/{id}"})
        post = find_ep(self.model, "POST", "/api/v1/orders")
        self.assertEqual(post.properties["auth"], ["authenticate", "requireRole('orders:write')"])
        self.assertEqual(post.properties["validation"], ["validate(createOrderSchema)"])
        self.assertEqual(post.properties["feature_flags"], ["manual-review"])
        self.assertEqual(post.properties["responses"], [201, 409])
        delete = find_ep(self.model, "DELETE", "/api/v1/orders/{id}")
        self.assertEqual(delete.properties["responses"], [204, 404])
        self.assertEqual(find_ep(self.model, "GET", "/health").title, "Health check")

    def test_labels(self):
        post = find_ep(self.model, "POST", "/api/v1/orders")
        ls = labels(post)
        for expected in ("If total > 1000 and feature flag manual-review is on", "Create order", "Publish ORDER_PLACED to 'order-events'",
                         "Call payments service: POST /v2/charges", "Respond 201 Created with order", "Respond 409 Conflict"):
            self.assertIn(expected, ls, ls)


class FastapiFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = scan(fixture("fastapi-orders"))

    def test_routers_depends_and_exceptions(self):
        ids = {e.id for e in self.model.endpoints}
        self.assertEqual(ids, {"GET /healthz", "GET /api/v1/orders/{order_id}", "POST /api/v1/orders", "POST /api/v1/orders/{order_id}/cancel"})
        post = find_ep(self.model, "POST", "/api/v1/orders")
        self.assertEqual(post.properties["status"], 201)
        self.assertEqual(post.properties["body"], "CreateOrderRequest")
        self.assertIn("Depends(require_scope('orders:write'))", post.properties["auth"])
        ls = labels(post)
        for expected in ("Call inventory service: POST /reservations", "Insert order", "Commit transaction",
                         "Publish message to 'order-events'", "Fail with 409 Conflict", "Respond 201 Created with order out"):
            self.assertIn(expected, ls, ls)
        get = find_ep(self.model, "GET", "/orders/{order_id}")
        self.assertEqual(get.properties["responses"], [200, 403, 404])
        self.assertIn("Load order by ID", labels(get))


class GoFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = scan(fixture("go-orders"))

    def test_chi_routes_and_receiver_resolution(self):
        ids = {e.id for e in self.model.endpoints}
        self.assertEqual(ids, {"GET /healthz", "GET /api/v1/orders/{id}", "POST /api/v1/orders", "POST /api/v1/orders/{id}/cancel"})
        post = find_ep(self.model, "POST", "/api/v1/orders")
        self.assertIn('handlers.RequireScope("orders:write")', post.properties["auth"])
        self.assertEqual(post.properties["responses"], [201, 400, 409, 500])
        ls = labels(post)
        for expected in ("Parse request body", "Place order", "Run SQL INSERT on orders", "Publish message to 'order-events'",
                         "Respond 201 Created with order", "On error, fail"):
            self.assertIn(expected, ls, ls)


if __name__ == "__main__":
    unittest.main()
