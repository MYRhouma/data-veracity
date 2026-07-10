"""FastAPI application factory and CLI entrypoint for the DVA VC Manager."""

from __future__ import annotations

import logging

from fastapi import FastAPI

from .config import cfg, setup_logging
from .routes import admin_router, router


def _build_production_whitelist():
    import asyncio

    import asyncpg

    from .whitelist import PgWhitelist

    if not cfg.postgres_dsn:
        raise RuntimeError(
            "DVA_VC_MANAGER_DB_URL is not set — cannot boot PgWhitelist. "
            "Either set it or override the get_whitelist dependency for tests."
        )
    pool = asyncio.run(asyncpg.create_pool(dsn=cfg.postgres_dsn, min_size=1, max_size=4))
    repo = PgWhitelist(pool)
    asyncio.run(repo._ensure_schema())
    return repo


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(
        title="DVA VC Manager",
        description=(
            "Issues and verifies Attestation of Veracity (AoV) credentials as "
            "W3C VC 2.0 JSON-LD JWS (Ed25519/EdDSA) using PyNaCl. Hosted at "
            "each Participant. Called by the DVA API during credential "
            "issuance in the synchronous attestation flow."
        ),
        version="0.1.0",
    )
    app.include_router(router)
    app.include_router(admin_router)
    return app


app = create_app()


def _level_to_str(level: int) -> str:
    for name, val in logging._levelToName.items():
        if val == level:
            return name.lower()
    return "info"


def cli() -> None:
    import uvicorn

    uvicorn.run(
        "dva_vc_manager.main:app",
        host=cfg.host,
        port=cfg.port,
        log_level=_level_to_str(cfg.log_level),
    )