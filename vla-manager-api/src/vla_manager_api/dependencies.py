"""FastAPI dependency providers.

Kept separate from :mod:`.main` and :mod:`.routes` to avoid circular
imports — :mod:`.main` imports :mod:`.routes` which imports
:mod:`.dependencies`. Tests override providers via
``app.dependency_overrides``.
"""

from __future__ import annotations

import logging
import os

from .config import cfg
from .repo import FakeVLARepo, VLARepo

logger = logging.getLogger(__name__)

# Lazy singleton — populated on first request. Tests override via
# ``app.dependency_overrides[get_repo] = lambda: FakeVLARepo()``.
_repo_singleton: VLARepo | None = None


async def get_repo() -> VLARepo:
    global _repo_singleton
    if _repo_singleton is None:
        if cfg.postgres_dsn:
            from .main import _build_production_repo

            _repo_singleton = _build_production_repo()
        else:
            # Dev convenience: boot with an in-memory repo so a bare
            # ``uvicorn vla_manager_api.main:app`` works without a
            # Postgres. State is lost on restart, so do NOT use this
            # mode in production — set VLA_MANAGER_DB_URL.
            logger.warning(
                "VLA_MANAGER_DB_URL is not set — falling back to FakeVLARepo "
                "(in-memory). State will be lost on restart. Configure "
                "VLA_MANAGER_DB_URL for production use."
            )
            _repo_singleton = FakeVLARepo()
    return _repo_singleton


def install_repo_for_tests(repo: VLARepo) -> None:
    """Bypass the lazy path and inject a fixed repo for tests."""
    global _repo_singleton
    _repo_singleton = repo