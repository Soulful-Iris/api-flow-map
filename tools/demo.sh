#!/usr/bin/env bash
# Builds a throw-away git repo from the bundled Spring fixture, makes a "PR" on a
# branch (threshold change, auth change, status-code change, new flag-gated call,
# removed endpoint, newly implemented endpoint), runs the diff and opens the review.
#
#   tools/demo.sh              -> /tmp/apiflow-demo
#   tools/demo.sh ~/some/dir   -> custom location
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
SKILL="$HERE/plugins/api-flow-map/skills/api-flow-map/scripts"
DEMO="${1:-/tmp/apiflow-demo}"
G="git -c user.email=demo@example.com -c user.name=demo"

rm -rf "$DEMO"
cp -R "$SKILL/tests/fixtures/spring-orders" "$DEMO"
cd "$DEMO"
git init -q -b main
$G add -A && $G commit -qm "base: orders service"
git checkout -qb feature/fraud-tuning

python3 - <<'PY'
import pathlib, re
svc = pathlib.Path("src/main/java/com/acme/orders/service/OrderServiceImpl.java"); s = svc.read_text()
s = s.replace("if (score > 80) {", "if (score > 60) {")
s = s.replace("        Order saved = orderRepository.save(order);\n        eventPublisher.publish(new OrderPlacedEvent(saved.getId()));\n        return saved;",
              "        Order saved = orderRepository.save(order);\n        eventPublisher.publish(new OrderPlacedEvent(saved.getId()));\n"
              "        if (featureFlags.isEnabled(\"order-confirmation-email\")) {\n            notificationClient.sendConfirmation(saved.getId(), request.getEmail());\n        }\n        return saved;")
s = s.replace("    private final FeatureFlags featureFlags;\n", "    private final FeatureFlags featureFlags;\n    private final NotificationClient notificationClient;\n")
s = s.replace("import com.acme.orders.client.InventoryClient;", "import com.acme.orders.client.InventoryClient;\nimport com.acme.orders.client.NotificationClient;")
svc.write_text(s)
pathlib.Path("src/main/java/com/acme/orders/client/NotificationClient.java").write_text(
    "package com.acme.orders.client;\n\nimport org.springframework.cloud.openfeign.FeignClient;\nimport org.springframework.web.bind.annotation.*;\n\n"
    "@FeignClient(name = \"notification-service\")\npublic interface NotificationClient {\n    @PostMapping(\"/emails/order-confirmation\")\n"
    "    void sendConfirmation(@RequestParam(\"orderId\") Long orderId, @RequestParam(\"email\") String email);\n}\n")
ctl = pathlib.Path("src/main/java/com/acme/orders/api/OrderController.java"); c = ctl.read_text()
c = c.replace("@PreAuthorize(\"hasRole('ORDER_READ')\")", "@PreAuthorize(\"hasRole('ORDER_ADMIN')\")")
c = c.replace("        orderService.cancel(id);\n        return ResponseEntity.noContent().build();", "        orderService.cancel(id);\n        return ResponseEntity.ok().build();")
c = re.sub(r"\n    @GetMapping\n    public List<OrderDto> listOrders.*?\n    }\n", "\n", c, flags=re.S)
c = c.replace("\n}\n", "\n    @GetMapping(\"/{id}/receipt\")\n    public ResponseEntity<byte[]> receipt(@PathVariable Long id) {\n        Order order = orderService.getOrder(id);\n"
              "        if (order == null) {\n            throw new OrderNotFoundException(id);\n        }\n        byte[] pdf = receiptRenderer.render(order);\n        return ResponseEntity.ok(pdf);\n    }\n}\n")
c = c.replace("    private final OrderMapper orderMapper;\n", "    private final OrderMapper orderMapper;\n    private final ReceiptRenderer receiptRenderer;\n")
ctl.write_text(c)
pathlib.Path("src/main/java/com/acme/orders/api/ReceiptRenderer.java").write_text(
    "package com.acme.orders.api;\nimport com.acme.orders.domain.Order;\nimport org.springframework.stereotype.Component;\nimport software.amazon.awssdk.services.s3.S3Client;\n\n"
    "@Component\npublic class ReceiptRenderer {\n    private final S3Client s3Client;\n    public ReceiptRenderer(S3Client s3Client) { this.s3Client = s3Client; }\n"
    "    public byte[] render(Order order) {\n        byte[] template = s3Client.getObjectAsBytes(b -> b.bucket(\"receipts\").key(\"template.pdf\")).asByteArray();\n        return template;\n    }\n}\n")
PY
$G add -A && $G commit -qm "fraud tuning, receipt endpoint, cancel returns 200"

echo
echo "== diff feature/fraud-tuning against main =="
python3 "$SKILL/apiflow.py" diff "$DEMO" --base main -o "$DEMO/apiflow-out"
echo
echo "Review:  $DEMO/apiflow-out/flow-diff.html   (Whole PR button = every changed endpoint, before/after)"
echo "Comment: $DEMO/apiflow-out/flow-diff.md"
if command -v open >/dev/null 2>&1; then open "$DEMO/apiflow-out/flow-diff.html"; fi
