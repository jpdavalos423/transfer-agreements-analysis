import unittest


class FastAPISmokeTest(unittest.TestCase):
    def test_fastapi_health_endpoint(self):
        try:
            from fastapi.testclient import TestClient
        except Exception as exc:  # pragma: no cover
            self.skipTest(f"FastAPI test client unavailable: {exc}")

        from apps.backend.main import create_app

        app = create_app()
        client = TestClient(app)
        response = client.get("/v1/health")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload.get("version"), "v1")
        self.assertIn(payload.get("status"), {"ok", "degraded"})


if __name__ == "__main__":
    unittest.main()
