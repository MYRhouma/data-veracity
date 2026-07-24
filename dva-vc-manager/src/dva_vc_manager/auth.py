"""Minimal Bearer-token auth for the admin endpoints.

Mirrors the inline guard the Kotlin ``route/adminRoutes.kt`` uses: when
``DVA_VC_MANAGER_API_KEY`` is empty, admin endpoints are disabled
entirely; otherwise require ``Authorization: Bearer <key>``.
"""

from __future__ import annotations

from fastapi import Header, HTTPException, status

from .config import cfg


def require_api_key(authorization: str | None = Header(default=None)) -> None:
    if cfg.api_key == "":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "API key not configured")
    header = (authorization or "").removeprefix("Bearer ").strip()
    if header != cfg.api_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")