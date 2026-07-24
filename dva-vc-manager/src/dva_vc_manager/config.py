"""Runtime configuration for the DVA VC Manager.

Mirrors the ``vla_manager_api.config`` shape (plain dataclass +
envvars).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from sys import stderr


def _truthy(value: str | None) -> bool:
    return value is not None and value.lower() in {"1", "true", "yes", "on"}


def _log_level(value: str | None) -> int:
    return getattr(logging, (value or "INFO").upper(), logging.INFO)


@dataclass
class Config:
    host: str = os.getenv("DVA_VC_MANAGER_HOST", "0.0.0.0")
    port: int = int(os.getenv("DVA_VC_MANAGER_PORT", "8000"))
    log_level: int = _log_level(os.getenv("DVA_VC_MANAGER_LOG_LEVEL", "INFO"))

    # Ed25519 signing key file path. Loaded on first use; created and
    # persisted (0600) if missing. Mirrors ``SigningKeyStore.kt:34``.
    signing_key_path: str = os.getenv("DVA_VC_MANAGER_SIGNING_KEY_PATH", "/data/dva-vc-signing-key.pem")

    # Optional shared-secret bearer auth for the admin endpoints.
    api_key: str = os.getenv("DVA_VC_MANAGER_API_KEY", "")

    # Postgres DSN (whitelist). Required for the production (asyncpg)
    # whitelist repo; empty → fall back to in-memory ``FakeWhitelist``.
    postgres_dsn: str = os.getenv("DVA_VC_MANAGER_DB_URL", "")


cfg = Config()


def setup_logging() -> None:
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