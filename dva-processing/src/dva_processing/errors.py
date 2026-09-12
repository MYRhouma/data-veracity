"""
Error responses shaped like the spec's ``Error`` schema.

Every error response the service raises itself is a ``{type, title,
detail}`` problem object. FastAPI instead wraps whatever an
``HTTPException`` is given under a ``detail`` key, so this module supplies
both halves: a :func:`http_error` helper for raise sites, and the handler
that renders the payload at the top level.

Request-body validation is deliberately left alone — those stay as
FastAPI's own ``422`` with its ``{"detail": [...]}`` array, which the spec
documents separately.
"""

from http import HTTPStatus
from typing import Optional

from fastapi import HTTPException
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from .eval import UnknownEngineError
from .model import ErrDTO


def http_error(
    status_code: int,
    title: str,
    detail: Optional[str] = None,
    type: Optional[str] = None,
) -> HTTPException:
    """
    Build an ``HTTPException`` whose detail is an ``Error`` payload.

    ``type`` defaults to the HTTP status constant (``404`` →
    ``NOT_FOUND``), which keeps the raise sites to a single line.
    """
    return HTTPException(
        status_code,
        detail=ErrDTO(
            type=type or HTTPStatus(status_code).name, title=title, detail=detail
        ).model_dump(exclude_none=True),
    )


def _as_problem(status_code: int, detail: object) -> ErrDTO:
    """Coerce an exception detail into the spec's ``Error`` shape."""
    if isinstance(detail, dict) and {"type", "title"} <= detail.keys():
        return ErrDTO.model_validate(detail)

    status = HTTPStatus(status_code)
    title = detail if isinstance(detail, str) and detail else status.phrase
    return ErrDTO(type=status.name, title=str(title))


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Render ``HTTPException`` as ``{type, title}`` rather than ``{detail}``."""
    return JSONResponse(
        status_code=exc.status_code,
        content=_as_problem(exc.status_code, exc.detail).model_dump(exclude_none=True),
        headers=getattr(exc, "headers", None),
    )


async def unknown_engine_handler(
    request: Request, exc: UnknownEngineError
) -> JSONResponse:
    """
    Answer a requirement naming an engine we cannot run with a ``400``.

    ODCS leaves ``DataQuality.engine`` a free-form string, so this is a
    body the framework cannot reject for us — it only surfaces once an
    evaluation reaches for the engine.
    """
    return JSONResponse(
        status_code=HTTPStatus.BAD_REQUEST,
        content=ErrDTO(
            type="UNKNOWN_ENGINE",
            title="Unknown quality engine",
            detail=str(exc),
        ).model_dump(),
    )
