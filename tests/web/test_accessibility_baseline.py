from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_HTML = REPO_ROOT / "apps" / "web" / "index.html"
STYLES_CSS = REPO_ROOT / "apps" / "web" / "styles.css"


class _StartTagCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.nodes: list[tuple[str, dict[str, str]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.nodes.append((tag, {k: v or "" for k, v in attrs}))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.nodes.append((tag, {k: v or "" for k, v in attrs}))


class AccessibilityBaselineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = INDEX_HTML.read_text(encoding="utf-8")
        cls.css = STYLES_CSS.read_text(encoding="utf-8")
        parser = _StartTagCollector()
        parser.feed(cls.html)
        cls.nodes = parser.nodes

    def _find_nodes(self, tag: str | None = None, **attrs: str) -> list[tuple[str, dict[str, str]]]:
        matches: list[tuple[str, dict[str, str]]] = []
        for node_tag, node_attrs in self.nodes:
            if tag is not None and node_tag != tag:
                continue
            if all(node_attrs.get(k) == v for k, v in attrs.items()):
                matches.append((node_tag, node_attrs))
        return matches

    def _has_id(self, element_id: str) -> bool:
        return any(attrs.get("id") == element_id for _, attrs in self.nodes)

    def test_labels_are_associated_with_form_controls(self):
        required_ids = {"college_id", "target_ucs", "ge_pattern", "completed_courses"}
        label_fors = {
            attrs.get("for")
            for tag, attrs in self.nodes
            if tag == "label" and attrs.get("for")
        }
        self.assertTrue(required_ids.issubset(label_fors))
        for control_id in required_ids:
            controls = self._find_nodes(id=control_id)
            self.assertTrue(controls, f"Missing control id='{control_id}'")

    def test_multiselect_has_describedby_help_text(self):
        target_nodes = self._find_nodes("select", id="target_ucs")
        self.assertEqual(len(target_nodes), 1)
        _, attrs = target_nodes[0]
        self.assertIn("multiple", attrs)
        self.assertEqual(attrs.get("aria-describedby"), "target-ucs-help")
        self.assertTrue(self._has_id("target-ucs-help"))

    def test_live_regions_present_for_feedback_panels(self):
        for panel_id in ["setup-errors-panel", "api-error-panel", "status-panel", "results-panel"]:
            nodes = self._find_nodes("section", id=panel_id)
            self.assertEqual(len(nodes), 1, f"Missing section '{panel_id}'")
            self.assertEqual(nodes[0][1].get("aria-live"), "polite")

    def test_focus_visible_and_mobile_layout_rules_exist(self):
        self.assertIn(":focus-visible", self.css)
        self.assertIn(".skip-link:focus-visible", self.css)
        self.assertRegex(self.css, r"@media\s*\(max-width:\s*640px\)")
        self.assertIn(".results-layout", self.css)
        self.assertRegex(self.css, r"\.results-layout\s*\{[^}]*grid-template-columns:\s*1fr\s*;\s*\}",)


if __name__ == "__main__":
    unittest.main()
