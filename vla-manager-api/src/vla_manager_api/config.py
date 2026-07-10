"""Runtime configuration for the VLA Manager API.

Read from environment variables (mirrors dva-processing's config style —
plain module-level constants instead of a config dataclass, so the rest
of the codebase can ``from .config import cfg``).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from sys import stderr


def _truthy(value: str | None) -> bool:
    return value is not None and value.lower() in {"1", "true", "yes", "on"}


def _log_level(value: str | None) -> int:
    import logging

    return getattr(logging, (value or "INFO").upper(), logging.INFO)


@dataclass
class Config:
    host: str = os.getenv("VLA_MANAGER_API_HOST", "0.0.0.0")
    port: int = int(os.getenv("VLA_MANAGER_API_PORT", "8000"))
    log_level: int = _log_level(os.getenv("VLA_MANAGER_API_LOG_LEVEL", "INFO"))

    # Postgres DSN. Required for the production (asyncpg) repository.
    # Example: postgresql://vla:vla@postgres-vla:5432/vla
    postgres_dsn: str = os.getenv("VLA_MANAGER_DB_URL", "")

    postgres_user: str = os.getenv("VLA_MANAGER_DB_USER", "")
    postgres_password: str = os.getenv("VLA_MANAGER_DB_PASSWORD", "")

    # Optional shared-secret bearer token guarding destructive endpoints
    # (DELETE /vla). When empty (default), ``DELETE /vla`` is disabled
    # entirely — mirrors the dva-api guard at vlaRoutes.kt:129-146.
    api_key: str = os.getenv("VLA_MANAGER_API_KEY", "")


cfg = Config()


def setup_logging() -> None:
    # Defer structlog import until called so unit tests importing `config`
    # don't drag structlog in (keeps test-time imports minimal).
    import structlog
    from structlog import make_filtering_bound_logger
    from structlog.dev import ConsoleRenderer
    from structlog.processors import JSONRenderer, StackInfoRenderer, TimeStamper
    from structlog.stdlib import add_log_level

    shared = [add_log_level, StackInfoRenderer(), TimeStamper(fmt="iso")]
    processors = shared + ([ConsoleRenderer()] if stderr.isatty() else [JSONRenderer()])
    structlog.configure(
        processors=processors,
        context_class=dict,
        wrapper_class=make_filtering_bound_logger(cfg.log_level),
    )