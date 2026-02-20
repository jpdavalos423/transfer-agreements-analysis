import unittest

from tests.api_fastapi.parity_harness import semantic_parity_compare


class ParityComparatorTest(unittest.TestCase):
    def test_ignores_allowed_volatile_fields(self):
        std = {"version": "v1", "request_id": "a", "meta": {"trace_id": "x"}}
        fast = {"version": "v1", "request_id": "b", "meta": {"trace_id": "y"}}

        ok, diff = semantic_parity_compare(std, fast)

        self.assertTrue(ok)
        self.assertEqual(diff, "")

    def test_reports_readable_path_diff(self):
        std = {"version": "v1", "plan": [{"term": "Term 1", "courses": []}]}
        fast = {"version": "v1", "plan": [{"term": "Term X", "courses": []}]}

        ok, diff = semantic_parity_compare(std, fast)

        self.assertFalse(ok)
        self.assertIn("$.plan[0].term", diff)
        self.assertIn("Unified diff:", diff)
        self.assertIn("--- stdlib", diff)
        self.assertIn("+++ fastapi", diff)


if __name__ == "__main__":
    unittest.main()
