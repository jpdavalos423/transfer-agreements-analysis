"""Pure service-layer seams for API handlers."""

from apps.api.services.metadata import (
    build_health_response,
    build_metadata_aggregate_response,
    build_metadata_colleges_response,
    build_metadata_districts_response,
    build_metadata_ucs_response,
)
from apps.api.services.pathways import (
    GeneratePathwayInput,
    PathwayServiceError,
    generate_pathway,
)

__all__ = [
    "GeneratePathwayInput",
    "PathwayServiceError",
    "build_health_response",
    "build_metadata_aggregate_response",
    "build_metadata_colleges_response",
    "build_metadata_districts_response",
    "build_metadata_ucs_response",
    "generate_pathway",
]
