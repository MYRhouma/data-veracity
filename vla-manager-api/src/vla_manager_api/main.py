"""FastAPI application factory and CLI entrypoint.

The application is wired so the repository implementation is resolved
through FastAPI's dependency-injection system. In production the
async-backed ``PgVLARepo`` is constructed on startup (via the lazy
``dependencies.get_repo``); in tests the caller swaps it via
``app.dependency_overrides[get_repo]``.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI

from .config import cfg, setup_logging
from .routes import router


def _build_production_repo():
    """Construct the async-backed repository.

    Requires ``cfg.postgres_dsn`` to be set (env ``VLA_MANAGER_DB_URL``).
    """
    import asyncio

    import asyncpg

    from .repo import PgVLARepo

    if not cfg.postgres_dsn:
        raise RuntimeError(
            "VLA_MANAGER_DB_URL is not set — cannot boot PgVLARepo. "
            "Either set it or override the get_repo dependency for tests."
        )

    pool = asyncio.run(asyncpg.create_pool(dsn=cfg.postgres_dsn, min_size=1, max_size=4))
    repo = PgVLARepo(pool)
    asyncio.run(repo._ensure_schema())
    return repo


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(
        title="VLA Manager API",
        description=(
            "Sole owner of Veracity Level Agreements, hosted at the Data "
            "Intermediary. Serves ``GET /vla/{id}`` to each participant's "
            "DVA API during attestation (steps 2-3 of the synchronous flow) "
            "and serves the VLA authoring UI for VLA CRUD."
        ),
        version="0.1.0",
    )
    app.include_router(router)
    return app


# Module-level app — used by ``uvicorn vla_manager_api.main:app`` and by
# the ``TestClient`` in ``tests/test_vla_crud.py``.
app = create_app()


def _level_to_str(level: int) -> str:
    for name, val in logging._levelToName.items():
        if val == level:
            return name.lower()
    return "info"


def cli() -> None:
    """uvicorn entrypoint (see ``[project.scripts]`` in pyproject.toml)."""
    import uvicorn

    uvicorn.run(
        "vla_manager_api.main:app",
        host=cfg.host,
        port=cfg.port,
        log_level=_level_to_str(cfg.log_level),
    )