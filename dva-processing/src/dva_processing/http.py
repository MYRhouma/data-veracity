"""FastAPI application factory for the DVA Processing module."""

from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, HTTPException, status
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import OPENAPI_FILE
from .errors import http_exception_handler, unknown_engine_handler
from .eval import UnknownEngineError
from .log import get_logger
from .routes import router

logger = get_logger()


def _load_openapi_schema(app: FastAPI) -> dict[str, Any]:
    """Return the hand-written spec, or FastAPI's generated one if absent."""
    try:
        with open(OPENAPI_FILE, encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    except FileNotFoundError:
        logger.warning(
            "OpenAPI spec not found, falling back to the auto-generated schema; "
            "set DVA_PROCESSING_OPENAPI_FILE to the hand-written spec",
            openapi_file=OPENAPI_FILE,
        )
        return get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )


def create_app() -> FastAPI:
    app = FastAPI(
        title="DVA Processing",
        description=(
            "Stateless veracity-check engine. Evaluates data-quality "
            "requirements expressed as ODCS DataQuality entries against "
            "supplied data."
        ),
        version="0.1.0",
        # Docs pages are FastAPI's own; the schema behind them is the
        # hand-written spec assigned below.
        docs_url="/swagger",
        redoc_url="/redoc",
        openapi_url="/swagger/openapi.json",
    )
    app.include_router(router)

    # Render errors as the spec's {type, title} rather than FastAPI's
    # {detail}. Body validation keeps FastAPI's own 422, which the spec
    # documents separately.
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(UnknownEngineError, unknown_engine_handler)

    @app.get("/swagger/components.yaml", include_in_schema=False)
    async def shared_schemas() -> FileResponse:
        """Serve the schemas the spec shares with the other DVA components.

        The spec refers to them as ``./components.yaml#/schemas/...``, which the
        docs page resolves against the URL it loaded the spec from, ie next to
        ``openapi_url``.  Keeping the reference external means the shared
        document stays the single definition rather than being copied in.
        """
        shared = Path(OPENAPI_FILE).parent / "components.yaml"
        if not shared.is_file():
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "No shared schemas available"
            )
        return FileResponse(shared, media_type="application/yaml")

    # Populating openapi_schema is what app.openapi() consults first, so
    # Swagger UI and ReDoc both render the hand-written spec.
    app.openapi_schema = _load_openapi_schema(app)

    return app


app = create_app()
