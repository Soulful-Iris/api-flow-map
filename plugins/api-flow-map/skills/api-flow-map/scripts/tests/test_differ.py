import os
import shutil
import subprocess
import tempfile
import unittest

from .helpers import fixture
from apiflow import gitutil, render_html, render_md
from apiflow.differ import diff_models
from apiflow.scanner import scan

CONTROLLER = "src/main/java/com/acme/orders/api/OrderController.java"
SERVICE = "src/main/java/com/acme/orders/service/OrderServiceImpl.java"


def _git(root, *args):
    subprocess.run(["git", "-C", root, *args], check=True, capture_output=True)


class DiffScenario(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="apiflow-test-")
        cls.root = os.path.join(cls.tmp, "repo")
        shutil.copytree(fixture("spring-orders"), cls.root)
        _git(cls.root, "init", "-q", "-b", "main")
        _git(cls.root, "config", "user.email", "t@t")
        _git(cls.root, "config", "user.name", "t")
        _git(cls.root, "add", "-A")
        _git(cls.root, "commit", "-qm", "base")
        _git(cls.root, "checkout", "-qb", "feature")
        # 1. condition change, 2. auth change, 3. new outbound call behind a flag, 4. status code change, 5. cosmetic edits
        svc = open(os.path.join(cls.root, SERVICE)).read()
        svc = svc.replace("if (score > 80) {", "if (score > 60) {")
        svc = svc.replace("        return saved;\n    }\n\n    @Override\n    @Transactional\n    public void cancel",
                          "        if (featureFlags.isEnabled(\"order-confirmation-email\")) {\n            paymentClient.refund(\"noop\");\n        }\n        return saved;\n    }\n\n    @Override\n    @Transactional\n    public void cancel")
        svc = svc.replace("Order order = Order.from(request);", "// build the aggregate\n        Order order = Order.from(request);")   # cosmetic
        open(os.path.join(cls.root, SERVICE), "w").write(svc)
        ctl = open(os.path.join(cls.root, CONTROLLER)).read()
        ctl = ctl.replace("hasRole('ORDER_READ')", "hasRole('ORDER_ADMIN')")
        ctl = ctl.replace("return ResponseEntity.noContent().build();", "return ResponseEntity.ok().build();")
        open(os.path.join(cls.root, CONTROLLER), "w").write(ctl)
        # working tree change (uncommitted) must be included too
        _git(cls.root, "commit", "-qam", "changes")
        base_ref = gitutil.default_base(cls.root)
        mb = gitutil.merge_base(cls.root, base_ref, "HEAD")
        snap = gitutil.snapshot(cls.root, mb)
        try:
            cls.base = scan(snap)
            cls.head = scan(cls.root)
        finally:
            gitutil.cleanup(snap)
        cls.diff = diff_models(cls.base, cls.head)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def ep(self, eid):
        for e in self.diff["endpoints"]:
            if e["id"] == eid:
                return e
        raise AssertionError(eid)

    def test_summary(self):
        s = self.diff["summary"]
        self.assertEqual(s["risk"], "high")
        self.assertEqual(s["endpoints_modified"], 3)
        self.assertEqual(s["endpoints_unchanged"], 2)   # list endpoint + spec-only receipt untouched
        self.assertEqual(s["endpoints_added"], 0)

    def test_condition_change_detected_not_cosmetic_edits(self):
        e = self.ep("POST /api/v1/orders")
        self.assertEqual(e["status"], "modified")
        reasons = [c["reason"] for c in e["flow_changes"]]
        self.assertTrue(any("If score > 80" in r and "If score > 60" in r for r in reasons), reasons)
        self.assertTrue(any(c["type"] == "added" and "feature flag" in c["reason"] for c in e["flow_changes"]), reasons)
        # the comment insertion shifted every line but nothing else may show up as changed
        self.assertEqual(e["counts"], {"added": 1, "removed": 0, "modified": 1})
        self.assertEqual(e["risk"], "medium")

    def test_auth_change_is_high_risk(self):
        e = self.ep("GET /api/v1/orders/{id}")
        self.assertEqual(e["risk"], "high")
        self.assertTrue(any(p["key"] == "auth" and "ORDER_ADMIN" in p["reason"] for p in e["property_changes"]))
        self.assertEqual(e["counts"], {"added": 0, "removed": 0, "modified": 0})

    def test_status_change_on_main_path(self):
        e = self.ep("POST /api/v1/orders/{id}/cancel")
        self.assertEqual(e["risk"], "high")
        mods = [c for c in e["flow_changes"] if c["type"] == "modified"]
        self.assertEqual(len(mods), 1)
        self.assertEqual(mods[0]["before"]["outcome"]["status"], 204)
        self.assertEqual(mods[0]["after"]["outcome"]["status"], 200)
        merged = e["flow"]
        ret = [n for n in merged if n["kind"] == "return"][0]
        self.assertEqual(ret["change"], "modified")
        self.assertEqual(ret["before"]["outcome"]["status"], 204)

    def test_renderers_produce_output(self):
        html = render_html.render(self.diff, "diff")
        self.assertIn("API change review", html)
        self.assertIn("hasRole(&#x27;ORDER_ADMIN&#x27;)", html) if "&#x27;" in html else self.assertIn("ORDER_ADMIN", html)
        self.assertNotIn("</script>\n<script>alert", html)
        md = render_md.render_diff(self.diff)
        self.assertIn("Status code changed 204 No Content → 200 OK", md)
        self.assertIn("```diff", md)
        scan_md = render_md.render_scan(self.head.to_dict())
        self.assertIn("```mermaid", scan_md)
        self.assertIn("flowchart TD", scan_md)

    def test_identical_models_have_no_changes(self):
        same = diff_models(self.head, scan(self.root))
        self.assertEqual(same["summary"]["risk"], "none")
        self.assertEqual(same["summary"]["endpoints_modified"], 0)
        self.assertTrue(all(e["status"] == "unchanged" for e in same["endpoints"]))


if __name__ == "__main__":
    unittest.main()


class CodeDiff(unittest.TestCase):
    def test_parse_unified_with_word_ranges(self):
        from apiflow import codediff
        text = """diff --git a/src/Svc.java b/src/Svc.java
index 1..2 100644
--- a/src/Svc.java
+++ b/src/Svc.java
@@ -10,3 +10,3 @@ class Svc {
     int score = scorer.score(order);
-    if (score > 80) {
+    if (score > 60) {
         hold(order);
"""
        files = codediff.parse_unified(text)
        self.assertEqual(len(files), 1)
        fd = files[0]
        self.assertEqual(fd["path"], "src/Svc.java")
        lines = fd["hunks"][0]["lines"]
        self.assertEqual([l["t"] for l in lines], [" ", "-", "+", " "])
        self.assertEqual(lines[1]["o"], 11)
        self.assertEqual(lines[2]["n"], 11)
        self.assertEqual(lines[1]["w"], [[16, 17]])   # the '8'
        self.assertEqual(lines[2]["w"], [[16, 17]])   # the '6'

    def test_collect_from_git_repo(self):
        from apiflow import codediff
        tmp = tempfile.mkdtemp(prefix="apiflow-cd-")
        try:
            root = os.path.join(tmp, "repo")
            os.makedirs(root)
            _git(root, "init", "-q", "-b", "main")
            _git(root, "config", "user.email", "t@t")
            _git(root, "config", "user.name", "t")
            open(os.path.join(root, "Svc.java"), "w").write("class Svc {\n  int limit() {\n    return 80;\n  }\n}\n")
            _git(root, "add", "-A")
            _git(root, "commit", "-qm", "base")
            base = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
            open(os.path.join(root, "Svc.java"), "w").write("class Svc {\n  int limit() {\n    return 60;\n  }\n}\n")   # uncommitted change
            open(os.path.join(root, "New.java"), "w").write("class New {}\n")                                            # untracked file
            out = codediff.collect(root, base, None, ["Svc.java", "New.java", "missing.java"])
            self.assertEqual(set(out["files"]), {"Svc.java", "New.java"})
            plus = [l for h in out["files"]["Svc.java"]["hunks"] for l in h["lines"] if l["t"] == "+"]
            self.assertEqual([l["s"] for l in plus], ["    return 60;"])
            self.assertEqual(out["files"]["New.java"]["status"], "added")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
