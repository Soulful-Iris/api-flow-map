"""The Mermaid a PR comment actually shows.

Four defects fixed here, each with a test that fails on the old behaviour:

  1. `/{id}` was rewritten to `/(id)`, printing an endpoint path that does not
     exist. Braces and brackets render correctly inside a quoted Mermaid node
     label; the escaping was never needed.
  2. Branch joins emitted an unlabelled `(( ))` circle, which reads as a
     rendering glitch rather than as structure.
  3. Every box repeated the call signature under the title, which is the
     opposite of this skill's own pitch and the main cause of sprawl.
  4. Nothing collapsed, so one endpoint became a 1700px diagram. The HTML view
     shows "7 steps inside"; the diagram now does too, and ONLY when nothing
     underneath it changed.

Verified against mermaid 12 with GitHub's own settings (securityLevel strict,
htmlLabels false) before the code was written.
"""
import unittest

from .helpers import fixture  # noqa: F401  (keeps tests importable as a package)
from apiflow.render_md import mermaid_flowchart


def ep(flow, path="/api/v1/orders/{id}/cancel", method="POST"):
    return {"id": f"{method} {path}", "method": method, "path": path, "flow": flow}


def call(label, children, change="same", tags=None):
    return {"kind": "call", "label": label, "children": children,
            "change": change, "tags": tags or [], "detail": f"{label}()"}


def step(label, kind="io.db", change="same"):
    return {"kind": kind, "label": label, "change": change, "tags": [],
            "detail": f"repo.{label.replace(' ', '')}()"}


class MermaidOutput(unittest.TestCase):

    def test_path_braces_survive(self):
        """The bug that printed a path nobody could call."""
        out = "\n".join(mermaid_flowchart(ep([step("Load order")])))
        self.assertIn("/api/v1/orders/{id}/cancel", out)
        self.assertNotIn("/(id)", out)

    def test_no_empty_join_nodes(self):
        flow = [{"kind": "branch", "label": "Depending on status",
                 "condition": "order.getStatus()", "change": "same", "tags": [],
                 "detail": "if (x)", "branches": [
                     {"label": "When CONFIRMED", "steps": [step("Refund payment")]},
                     {"label": "Otherwise", "steps": [step("Mark cancelled")]},
                 ]}]
        out = "\n".join(mermaid_flowchart(ep(flow)))
        self.assertNotIn("(( ))", out)

    def test_a_modified_step_shows_the_old_value_struck_through(self):
        flow = [{"kind": "return", "label": "Respond 200 OK", "change": "modified",
                 "tags": [], "detail": "return ok()",
                 "outcome": {"status": 200}, "changed_fields": ["outcome"],
                 "before": {"label": "Respond 204 No Content",
                            "outcome": {"status": 204}}}]
        out = "\n".join(mermaid_flowchart(ep(flow)))
        self.assertIn("<s>was Respond 204 No Content [204]</s>", out)

    def test_unchanged_internals_collapse(self):
        kids = [step("Load order"), step("Save order"), step("Publish event", "io.queue")]
        out = "\n".join(mermaid_flowchart(ep([call("Cancel order", kids)])))
        self.assertIn("3 steps inside", out)
        self.assertNotIn("Load order", out)

    def test_changed_internals_do_NOT_collapse(self):
        """Collapsing is for noise. A change underneath is the whole point of
        the diagram and must stay visible."""
        kids = [step("Load order"), step("Save order", change="added")]
        out = "\n".join(mermaid_flowchart(ep([call("Cancel order", kids)])))
        self.assertNotIn("steps inside", out)
        self.assertIn("Save order", out)

    def test_code_signatures_are_not_in_the_boxes(self):
        """`OrderServiceImpl.placeOrder(request, requestId)` under every title
        is what made these unreadable."""
        kids = [step("Load order"), step("Save order", change="added")]
        out = "\n".join(mermaid_flowchart(ep([call("Cancel order", kids)])))
        self.assertNotIn("repo.Loadorder()", out)
        self.assertNotIn("Cancel order()", out)

    def test_a_branch_condition_is_still_shown(self):
        """Conditions are meaning, not noise; they stay."""
        flow = [{"kind": "branch", "label": "If score is high",
                 "condition": "score > 60", "change": "same", "tags": [],
                 "detail": "if (score > 60)", "branches": []}]
        out = "\n".join(mermaid_flowchart(ep(flow)))
        self.assertIn("score &gt; 60".replace("&gt;", ">"), out)


if __name__ == "__main__":
    unittest.main()
