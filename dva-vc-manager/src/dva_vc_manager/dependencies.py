"""FastAPI dependency providers for the DVA VC Manager."""

from __future__ import annotations

import logging

from .config import cfg
from .whitelist import FakeWhitelist, WhitelistRepo

logger = logging.getLogger(__name__)

_whitelist_singleton: WhitelistRepo | None = None


async def get_whitelist() -> WhitelistRepo:
    global _whitelist_singleton
    if _whitelist_singleton is None:
        if cfg.postgres_dsn:
            from .main import _build_production_whitelist

            _whitelist_singleton = _build_production_whitelist()
        else:
            logger.warning(
                "DVA_VC_MANAGER_DB_URL is not set — falling back to "
                "FakeWhitelist (in-memory). Verifications will fail-closed "
                "until admin populates the whitelist via POST /admin/whitelist."
            )
            _whitelist_singleton = FakeWhitelist()
    return _whitelist_singleton


def install_whitelist_for_tests(repo: WhitelistRepo) -> None:
    global _whitelist_singleton
    _whitelist_singleton = repo