"""Pure metadata response builders used by API transport handlers."""

from __future__ import annotations

from typing import Any

from apps.api.metadata_service import RuntimeMetadata
from packages.shared_types.v1 import API_VERSION


def build_metadata_colleges_response(metadata: RuntimeMetadata) -> dict[str, Any]:
    return {
        "version": API_VERSION,
        "data": metadata.colleges,
    }


def build_metadata_districts_response(metadata: RuntimeMetadata) -> dict[str, Any]:
    return {
        "version": API_VERSION,
        "data": metadata.districts,
    }


def build_metadata_ucs_response(metadata: RuntimeMetadata) -> dict[str, Any]:
    return {
        "version": API_VERSION,
        "data": metadata.ucs,
    }


def build_metadata_aggregate_response(
    metadata: RuntimeMetadata,
    *,
    allowed_ge_patterns: set[str],
) -> dict[str, Any]:
    return {
        "version": API_VERSION,
        "colleges": metadata.colleges,
        "districts": metadata.districts,
        "ucs": metadata.ucs,
        "ge_patterns": sorted(allowed_ge_patterns),
    }


def build_health_response(metadata: RuntimeMetadata) -> dict[str, Any]:
    return {
        "version": API_VERSION,
        "status": "ok",
        "runtime": {
            "dataset_version": metadata.manifest.get("version", ""),
            "generated_at": metadata.manifest.get("generated_at", ""),
            "row_counts": metadata.manifest.get("row_counts", {}),
        },
    }
