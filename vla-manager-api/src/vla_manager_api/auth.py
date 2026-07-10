"""Minimal Bearer-token auth for destructive endpoints.

Mirrors the Kotlin guard at ``vlaRoutes.kt:129-146``: ``DELETE /vla``
is **disabled entirely** when ``VLA_MANAGER_API_KEY`` is empty, and
requires ``Authorization: Bearer <key>`` otherwise.

This module is intentionally minimal — shared-secret Bearer only. It is
reused by the VLA Manager Vue UI when deleting all VLAs.
"""

from __future__ import annotations

from fastapi import Header, HTTPException, status

from .config import cfg


def require_api_key(authorization: str | None = Header(default=None)) -> None:
    """Dependency that fails-closed when no API key is configured."""
    if cfg.api_key == "":
        # Gate removed: refuse all wipe attempts rather than allowing
        # unauthenticated mass deletion during dev/test runs.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "API key not configured")

    header = (authorization or "").removeprefix("Bearer ").strip()
    if header != cfg.api_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")