"""FastAPI application factory and CLI entrypoint for the DVA VC Manager."""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse

from .config import cfg, setup_logging
from .routes import admin_router, router

_SWAGGER_UI_HTML = """\
<!DOCTYPE html>
<html>
  <head>
    <title>DVA VC Manager — Swagger UI</title>
    <link href="https://unpkg.com/swagger-ui-dist@5.17.12/swagger-ui.css" rel="stylesheet">
    <link href="https://unpkg.com/swagger-ui-dist@5.17.12/favicon-32x32.png" rel="icon" type="image/x-icon">
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.17.12/swagger-ui-bundle.js" crossorigin="anonymous"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.17.12/swagger-ui-standalone-preset.js" crossorigin="anonymous"></script>
    <script>
      window.onload = function() {
        SwaggerUIBundle({
          url: '/swagger/openapi.yaml',
          dom_id: '#swagger-ui',
          deepLinking: false,
          presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
          layout: 'StandaloneLayout'
        });
      };
    </script>
  </body>
</html>
"""


def _build_production_whitelist():
    """Construct the async-backed whitelist repository.

    DEPRECATED sync stub — kept only for test-override compatibility.
    Production callers must use the async version below.
    """
    raise RuntimeError("Call _build_production_whitelist_async() from within an async context.")


async def _build_production_whitelist_async():
    """Construct the async-backed whitelist repository.

    Uses await (not asyncio.run) so it is safe to call from within the
    uvicorn event loop — mirrors _build_production_repo() in vla-manager-api.
    """
    import asyncpg

    from .whitelist import PgWhitelist

    if not cfg.postgres_dsn:
        raise RuntimeError(
            "DVA_VC_MANAGER_DB_URL is not set — cannot boot PgWhitelist. "
            "Either set it or override get_whitelist dependency for tests."
        )

    pool = await asyncpg.create_pool(dsn=cfg.postgres_dsn, min_size=1, max_size=4)
    repo = PgWhitelist(pool)
    await repo._ensure_schema()
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
        # Disable auto-generated docs — hand-written spec is served at /swagger
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.include_router(router)
    app.include_router(admin_router)

    @app.get("/swagger", response_class=HTMLResponse, include_in_schema=False)
    async def swagger_ui() -> HTMLResponse:
        """Serve the Swagger UI loaded from the hand-written OpenAPI spec."""
        return HTMLResponse(content=_SWAGGER_UI_HTML)

    @app.get("/swagger/openapi.yaml", response_class=PlainTextResponse, include_in_schema=False)
    async def swagger_spec() -> PlainTextResponse:
        """Serve the hand-written OpenAPI spec YAML from disk."""
        spec_path = os.environ.get("DVA_VC_MANAGER_OPENAPI_FILE", "/app/openapi.yaml")
        try:
            with open(spec_path, "r", encoding="utf-8") as fh:
                content = fh.read()
        except FileNotFoundError:
            return PlainTextResponse(content="# spec file not found", status_code=404)
        return PlainTextResponse(content=content, media_type="application/yaml")

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