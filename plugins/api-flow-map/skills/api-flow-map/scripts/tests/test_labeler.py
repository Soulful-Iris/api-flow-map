import unittest

from .helpers import fixture  # noqa: F401  (ensures sys.path)
from apiflow import labeler as L


class Conditions(unittest.TestCase):
    def check(self, cond, lang, expected):
        self.assertEqual(L.humanize_condition(cond, lang), expected)

    def test_java(self):
        self.check("!stock.isAvailable()", "java", "stock is not available")
        self.check("order.getTotal().compareTo(REVIEW_THRESHOLD) > 0", "java", "order total is greater than REVIEW_THRESHOLD")
        self.check("request.getItems() == null || request.getItems().isEmpty()", "java", "request items is missing or request items is empty")
        self.check("!StringUtils.isBlank(request.getPaymentToken())", "java", "request payment token is not blank")
        self.check("order.getStatus() == OrderStatus.CONFIRMED", "java", "order status is confirmed")
        self.check("user.hasRole('ADMIN') && !order.isLocked()", "java", "user has role ADMIN and order is not locked")

    def test_js_python_go(self):
        self.check("!order || order.status !== 'NEW'", "typescript", "order is missing or order status is not NEW")
        self.check("!isValid(payload)", "typescript", "payload is not valid")
        self.check("not user.is_active", "python", "user is not active")
        self.check("order is None or order.total <= 0", "python", "order is missing or order total ≤ 0")
        self.check("err != nil && !errors.Is(err, ErrNotFound)", "go", "an error occurred and the error is not not found")
        self.check("featureFlags.isEnabled(\"new-pricing\") && order.total > 100", "java", "feature flag new-pricing is on and order total > 100")


class Titles(unittest.TestCase):
    def test_endpoint_titles(self):
        self.assertEqual(L.endpoint_title("GET", "/api/v1/orders/{id}", "getOrder"), "Get order")
        self.assertEqual(L.endpoint_title("GET", "/api/v1/orders/{id}", "handle"), "Get order by ID")
        self.assertEqual(L.endpoint_title("POST", "/api/v1/orders/{id}/cancel", "inline"), "Cancel order")
        self.assertEqual(L.endpoint_title("GET", "/health", "inline"), "Health check")
        self.assertEqual(L.endpoint_title("GET", "/x", "x", spec_summary="Fetch an order."), "Fetch an order")
        self.assertEqual(L.endpoint_title("GET", "/x", "x", overrides={"GET /x": "Custom"}), "Custom")

    def test_return_types(self):
        self.assertEqual(L.return_words_from_type("ResponseEntity<List<OrderDto>>"), "list of order DTOs")
        self.assertEqual(L.return_words_from_type("Mono<Void>"), "")
        self.assertEqual(L.return_words_from_type("Task<ActionResult<OrderResponse>>"), "order response")
        self.assertEqual(L.return_words_from_type("(*store.Order, error)"), "order")
        self.assertEqual(L.return_words_from_type("ResponseEntity<byte[]>"), "binary content")

    def test_db_and_queue_labels(self):
        self.assertEqual(L.db_label("findById", "Order", "order repository"), "Load order by ID")
        self.assertEqual(L.db_label("findByCustomerIdOrderByCreatedAtDesc", "Order", ""), "Query orders by customer ID")
        self.assertEqual(L.db_label("save", "Order", ""), "Save order")
        self.assertEqual(L.db_label("query", "", "pool", "'SELECT * FROM orders WHERE id = $1'"), "Run SQL SELECT on orders")
        self.assertEqual(L.queue_label("send", "kafka template", "\"order-events\", new OrderPlacedEvent(id)"), "Publish OrderPlacedEvent to 'order-events' via Kafka")
        self.assertEqual(L.queue_label("publish", "", "'order-events', { type: 'ORDER_FLAGGED' }"), "Publish ORDER_FLAGGED to 'order-events'")

    def test_http_labels(self):
        self.assertEqual(L.http_label("payment-service", "POST /v2/charges", "charge"), "Call payment-service: POST /v2/charges")
        self.assertEqual(L.http_label("", "", "post", "`${PAYMENTS_URL}/v2/charges`, body"), "Call payments service: POST /v2/charges")
        self.assertEqual(L.http_label("", "", "postForObject", 'fraudUrl + "/score", order'), "Call fraud service: POST /score")


if __name__ == "__main__":
    unittest.main()
