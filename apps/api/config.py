"""Environment-backed API server configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 8000
_DEFAULT_CORS_ENABLED = True
_DEFAULT_LOG_LEVEL = "SILENT"
_ALLOWED_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "SILENT"}
_DEFAULT_CORS_ALLOWED_ORIGINS = (
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "http://127.0.0.1:4173",
    "http://localhost:4173",
    "http://127.0.0.1:5173",
    "http://localhost:5173",
)


@dataclass(frozen=True)
class APIServerConfig:
    host: str = _DEFAULT_HOST
    port: int = _DEFAULT_PORT
    cors_enabled: bool = _DEFAULT_CORS_ENABLED
    cors_allowed_origins: tuple[str, ...] = _DEFAULT_CORS_ALLOWED_ORIGINS
    log_level: str = _DEFAULT_LOG_LEVEL


def _parse_bool(raw: str | None, *, default: bool) -> bool:
    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _parse_port(raw: str | None, *, default: int) -> int:
    if raw is None:
        return default
    try:
        port = int(raw)
    except ValueError:
        return default
    if port < 1 or port > 65535:
        return default
    return port


def _parse_log_level(raw: str | None, *, default: str) -> str:
    if raw is None:
        return default
    level = raw.strip().upper()
    if level in _ALLOWED_LOG_LEVELS:
        return level
    return default


def _parse_origin_list(raw: str | None) -> tuple[str, ...]:
    if raw is None:
        return _DEFAULT_CORS_ALLOWED_ORIGINS
    parsed = []
    seen = set()
    for item in raw.split(","):
        origin = item.strip()
        if not origin or origin in seen:
            continue
        seen.add(origin)
        parsed.append(origin)
    return tuple(parsed)


def load_api_server_config_from_env(env: dict[str, str] | None = None) -> APIServerConfig:
    source = env if env is not None else os.environ
    host = source.get("TPP_API_HOST", _DEFAULT_HOST).strip() or _DEFAULT_HOST
    return APIServerConfig(
        host=host,
        port=_parse_port(source.get("TPP_API_PORT"), default=_DEFAULT_PORT),
        cors_enabled=_parse_bool(
            source.get("TPP_API_CORS_ENABLED"),
            default=_DEFAULT_CORS_ENABLED,
        ),
        cors_allowed_origins=_parse_origin_list(
            source.get("TPP_API_CORS_ALLOWED_ORIGINS")
        ),
        log_level=_parse_log_level(
            source.get("TPP_API_LOG_LEVEL"),
            default=_DEFAULT_LOG_LEVEL,
        ),
    )
