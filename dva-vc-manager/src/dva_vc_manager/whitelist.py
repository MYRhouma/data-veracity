"""Whitelist of trusted attester ``did:key`` identifiers.

The verify side is **fail-closed**: ``/aov/verify`` rejects any
verification when the whitelist is empty (mirrors
``aovRoutes.kt:231-242``). The whitelist is populated via admin
endpoints (``POST /admin/whitelist``) in the new DVA VC MANAGER service.

Two implementations:
* :class:`FakeWhitelist` — in-memory list for tests.
* :class:`PgWhitelist` — async-backed PostgreSQL repository via
  asyncpg; mirrors ``whitelistMapping.kt:17-20``.
"""

from __future__ import annotations

from typing import Any, Optional, Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel

__all__ = ["WhitelistEntry", "WhitelistRepo", "FakeWhitelist", "PgWhitelist"]


class WhitelistEntry(BaseModel):
    id: UUID
    did_key: str
    label: Optional[str] = None

    @classmethod
    def from_row(cls, row: Any) -> "WhitelistEntry":
        return cls(id=row["id"], did_key=row["did_key"], label=row["label"])


class WhitelistRepo(Protocol):
    async def all(self) -> list[WhitelistEntry]: ...
    async def add(self, did_key: str, label: Optional[str]) -> WhitelistEntry: ...
    async def remove(self, did_key: str) -> bool: ...
    async def find(self, did_key: str) -> Optional[WhitelistEntry]: ...
    async def contains(self, did_key: str) -> bool: ...


class FakeWhitelist:
    """In-memory whitelist for tests."""

    def __init__(self) -> None:
        self._entries: dict[str, WhitelistEntry] = {}

    async def all(self) -> list[WhitelistEntry]:
        return list(self._entries.values())

    async def add(self, did_key: str, label: Optional[str] = None) -> WhitelistEntry:
        if did_key in self._entries:
            return self._entries[did_key]
        entry = WhitelistEntry(id=uuid4(), did_key=did_key, label=label)
        self._entries[did_key] = entry
        return entry

    async def remove(self, did_key: str) -> bool:
        return self._entries.pop(did_key, None) is not None

    async def find(self, did_key: str) -> Optional[WhitelistEntry]:
        return self._entries.get(did_key)

    async def contains(self, did_key: str) -> bool:
        return did_key in self._entries


class PgWhitelist:
    """PostgreSQL whitelist (asyncpg)."""

    def __init__(self, pool):  # type: ignore[no-untyped-def]
        self._pool = pool

    async def _ensure_schema(self) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS did_key_whitelist (
                    id       UUID PRIMARY KEY,
                    did_key  VARCHAR(255) UNIQUE NOT NULL,
                    label    VARCHAR(255)
                )
                """
            )

    async def all(self) -> list[WhitelistEntry]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, did_key, label FROM did_key_whitelist"
            )
        return [WhitelistEntry.from_row(r) for r in rows]

    async def add(self, did_key: str, label: Optional[str] = None) -> WhitelistEntry:
        import json
        import asyncpg.exceptions
        id = uuid4()
        async with self._pool.acquire() as conn:
            try:
                await conn.execute(
                    "INSERT INTO did_key_whitelist (id, did_key, label) VALUES ($1, $2, $3)",
                    id, did_key, label,
                )
            except asyncpg.exceptions.UniqueViolationError:
                existing = await conn.fetchrow(
                    "SELECT id, did_key, label FROM did_key_whitelist WHERE did_key = $1",
                    did_key,
                )
                return WhitelistEntry.from_row(existing)
        return WhitelistEntry(id=id, did_key=did_key, label=label)

    async def remove(self, did_key: str) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM did_key_whitelist WHERE did_key = $1", did_key
            )
        return result.endswith("1")  # "DELETE 1" → true

    async def find(self, did_key: str) -> Optional[WhitelistEntry]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, did_key, label FROM did_key_whitelist WHERE did_key = $1",
                did_key,
            )
        return WhitelistEntry.from_row(row) if row is not None else None

    async def contains(self, did_key: str) -> bool:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT 1 FROM did_key_whitelist WHERE did_key = $1", did_key
            )
        return row is not None