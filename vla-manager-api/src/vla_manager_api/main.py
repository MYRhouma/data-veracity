"""FastAPI application factory and CLI entrypoint.

The application is wired so the repository implementation is resolved
through FastAPI's dependency-injection system. In production the
async-backed ``PgVLARepo`` is constructed on startup (via the lazy
``dependencies.get_repo``); in tests the caller swaps it via
``app.dependency_overrides[get_repo]``.
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, PlainTextResponse

from .config import cfg, setup_logging
from .routes import router
from .template_routes import router as template_router

_SWAGGER_UI_HTML = """\
<!DOCTYPE html>
<html>
  <head>
    <title>VLA Manager API — Swagger UI</title>
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


async def _build_production_repo():
    """Construct the async-backed repository.

    Requires ``cfg.postgres_dsn`` to be set (env ``VLA_MANAGER_DB_URL``).
    Must be awaited from within the running event loop (e.g. the
    ``get_repo`` dependency) — never wrapped in ``asyncio.run()``, which
    raises ``RuntimeError`` when a loop is already running.
    """
    import asyncpg

    from .repo import PgVLARepo

    if not cfg.postgres_dsn:
        raise RuntimeError(
            "VLA_MANAGER_DB_URL is not set — cannot boot PgVLARepo. "
            "Either set it or override the get_repo dependency for tests."
        )

    pool = await asyncpg.create_pool(dsn=cfg.postgres_dsn, min_size=1, max_size=4)
    repo = PgVLARepo(pool)
    await repo._ensure_schema()
    return repo


async def _build_production_template_repo():
    """Construct the async-backed Template repository.

    Shares the same asyncpg pool as the VLA repo but owns separate
    ``templates`` + ``evaluation_methods`` tables.
    """
    import asyncpg

    from .repo import PgTemplateRepo

    if not cfg.postgres_dsn:
        raise RuntimeError(
            "VLA_MANAGER_DB_URL is not set — cannot boot PgTemplateRepo. "
            "Either set it or override the get_template_repo dependency for tests."
        )

    pool = await asyncpg.create_pool(dsn=cfg.postgres_dsn, min_size=1, max_size=4)
    repo = PgTemplateRepo(pool)
    await repo._ensure_schema()
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
        # Disable auto-generated docs — hand-written spec is served at /swagger
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.include_router(router)
    app.include_router(template_router)

    @app.get("/swagger", response_class=HTMLResponse, include_in_schema=False)
    async def swagger_ui() -> HTMLResponse:
        """Serve the Swagger UI loaded from the hand-written OpenAPI spec."""
        return HTMLResponse(content=_SWAGGER_UI_HTML)

    @app.get("/swagger/openapi.yaml", response_class=PlainTextResponse, include_in_schema=False)
    async def swagger_spec() -> PlainTextResponse:
        """Serve the hand-written OpenAPI spec YAML from disk."""
        spec_path = os.environ.get("VLA_MANAGER_OPENAPI_FILE", "/app/openapi.yaml")
        try:
            with open(spec_path, "r", encoding="utf-8") as fh:
                content = fh.read()
        except FileNotFoundError:
            return PlainTextResponse(content="# spec file not found", status_code=404)
        return PlainTextResponse(content=content, media_type="application/yaml")

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