import unittest
from unittest.mock import patch

from apps.api.planner_service import PlannerServiceError
from apps.api.services.pathways import (
    GeneratePathwayInput,
    PathwayServiceError,
    generate_pathway,
)


class PathwayServiceLayerTest(unittest.TestCase):
    def test_generate_pathway_success_enriches_response(self):
        request = GeneratePathwayInput(
            college_id="de_anza",
            target_ucs=("UCLA", "UCSD"),
            ge_pattern="IGETC",
            completed_courses=("MATH 1A",),
            request_id="req-123",
        )
        runtime_manifest = {
            "version": "v1-runtime",
            "generated_at": "2026-02-19T00:00:00Z",
        }
        planner_response = {
            "version": "v1",
            "plan": [],
            "warnings": [
                {
                    "code": "PLANNER_NOT_IMPLEMENTED",
                    "message": "Planner not implemented.",
                }
            ],
            "meta": {
                "college_id": "de_anza",
                "target_ucs": ["UCLA", "UCSD"],
                "ge_pattern": "IGETC",
                "completed_courses_count": 1,
            },
        }

        with patch(
            "apps.api.services.pathways.generate_pathway_response",
            return_value=planner_response,
        ) as mocked_generate:
            response = generate_pathway(request, runtime_manifest=runtime_manifest)

        mocked_generate.assert_called_once_with(
            {
                "college_id": "de_anza",
                "target_ucs": ["UCLA", "UCSD"],
                "ge_pattern": "IGETC",
                "completed_courses": ["MATH 1A"],
            }
        )
        self.assertEqual(response["request_id"], "req-123")
        self.assertEqual(response["warnings"][0]["trace_id"], "req-123")
        self.assertEqual(response["warnings"][0]["severity"], "WARN")
        self.assertEqual(response["warnings"][0]["source"], "planner_core")
        self.assertEqual(
            response["meta"]["runtime"],
            {
                "dataset_version": "v1-runtime",
                "generated_at": "2026-02-19T00:00:00Z",
            },
        )

    def test_generate_pathway_wraps_planner_service_error(self):
        request = GeneratePathwayInput(
            college_id="de_anza",
            target_ucs=("UCLA",),
            ge_pattern="IGETC",
            completed_courses=(),
            request_id="req-456",
        )

        with patch(
            "apps.api.services.pathways.generate_pathway_response",
            side_effect=PlannerServiceError("runtime failed"),
        ):
            with self.assertRaises(PathwayServiceError) as exc_info:
                generate_pathway(request, runtime_manifest={"version": "v1"})

        err = exc_info.exception
        self.assertEqual(err.code, "PLANNER_RUNTIME_ERROR")
        self.assertEqual(err.status, 500)
        self.assertEqual(
            err.message,
            "Unable to generate pathway response from runtime artifacts.",
        )
        self.assertEqual(err.details[0]["field"], "planner_service")
        self.assertIn("runtime failed", err.details[0]["message"])


if __name__ == "__main__":
    unittest.main()
