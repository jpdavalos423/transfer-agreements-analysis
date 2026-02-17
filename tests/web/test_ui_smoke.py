import json
import threading
import unittest
import urllib.request

from apps.api.server import create_server as create_api_server
from apps.web.server import create_server as create_web_server


class WebUISmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api_server = create_api_server(host="127.0.0.1", port=0)
        cls.api_port = cls.api_server.server_address[1]
        cls.api_thread = threading.Thread(target=cls.api_server.serve_forever, daemon=True)
        cls.api_thread.start()

        cls.web_server = create_web_server(host="127.0.0.1", port=0)
        cls.web_port = cls.web_server.server_address[1]
        cls.web_thread = threading.Thread(target=cls.web_server.serve_forever, daemon=True)
        cls.web_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.web_server.shutdown()
        cls.web_server.server_close()
        cls.web_thread.join(timeout=2)

        cls.api_server.shutdown()
        cls.api_server.server_close()
        cls.api_thread.join(timeout=2)

    def test_ui_renders_and_submit_payload_shape_is_accepted(self):
        # Render check.
        with urllib.request.urlopen(f"http://127.0.0.1:{self.web_port}/index.html", timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            html = resp.read().decode("utf-8")

        self.assertIn('id="planner-form"', html)
        self.assertIn('id="college_id"', html)
        self.assertIn('id="target_ucs"', html)
        self.assertIn('id="ge_pattern"', html)
        self.assertIn('id="completed_courses"', html)

        # Submit-equivalent API check (basic smoke until browser automation is added).
        payload = {
            "college_id": "de_anza",
            "target_ucs": ["UCLA", "UCSD"],
            "ge_pattern": "IGETC",
            "completed_courses": ["MATH 1A"],
        }
        req = urllib.request.Request(
            url=f"http://127.0.0.1:{self.api_port}/v1/pathways/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            body = json.loads(resp.read().decode("utf-8"))

        self.assertEqual(body.get("version"), "v1")
        self.assertIsInstance(body.get("plan"), list)
        self.assertIsInstance(body.get("warnings"), list)


if __name__ == "__main__":
    unittest.main()

