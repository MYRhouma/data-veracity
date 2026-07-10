"""VLA repository — pluggable persistence for Veracity Level Agreements.

Two implementations:

* :class:`FakeVLARepo` — in-memory map used in tests (mirrors the Kotlin
  ``FakeVLARepo``). No external dependencies.
* :class:`PgVLARepo` — async-backed PostgreSQL repository via asyncpg.
  The repository owns the ``vlas`` table on the Data Intermediary's
  Postgres. Each VLA is stored as the raw ODCS JSON text in
  ``odcs_json``; the UUID primary key is generated on the application
  side (avoids any pgcrypto/extension dependency) and round-trips
  verbatim. The ``id`` field is injected into the returned JSON object
  on read — exactly as the Kotlin ``toModel()`` helper does.

The interface is async because the production path uses asyncpg; the
fake returns plain values for ease of testing.
"""

from __future__ import annotations

import json
from typing import Any, Optional, Protocol
from uuid import UUID, uuid4

__all__ = ["VLARepo", "FakeVLARepo", "PgVLARepo"]


class VLARepo(Protocol):
    """Minimal contract for VLA persistence."""

    async def all(self) -> list[dict[str, Any]]: ...

    async def by_id(self, id: UUID) -> Optional[dict[str, Any]]: ...

    async def add(self, vla: dict[str, Any]) -> Optional[UUID]: ...

    async def remove_all(self) -> None: ...


def _with_id(odcs_text: str, id: UUID) -> dict[str, Any]:
    """Inject the ``id`` field into a deserialised ODCS object."""
    obj: dict[str, Any] = json.loads(odcs_text)
    obj["id"] = str(id)
    return obj


class FakeVLARepo:
    """In-memory VLA repository for tests."""

    def __init__(self) -> None:
        self._vlas: dict[UUID, str] = {}

    async def all(self) -> list[dict[str, Any]]:
        return [_with_id(text, id) for id, text in self._vlas.items()]

    async def by_id(self, id: UUID) -> Optional[dict[str, Any]]:
        text = self._vlas.get(id)
        return _with_id(text, id) if text is not None else None

    async def add(self, vla: dict[str, Any]) -> Optional[UUID]:
        id = uuid4()
        # Strip any caller-supplied "id" before persisting — persistence
        # owns the id, not the caller.
        vla = {k: v for k, v in vla.items() if k != "id"}
        self._vlas[id] = json.dumps(vla)
        return id

    async def remove_all(self) -> None:
        self._vlas.clear()


class PgVLARepo:
    """Async-backed PostgreSQL VLA repository using asyncpg.

    Owns the ``vlas`` table. Constructed with an ``asyncpg.Pool`` (see
    :mod:`vla_manager_api.main` for pool creation). Columns mirror the
    Kotlin ``VLAsTable`` (``db/vlaMapping.kt:12-14``):

    ``id UUID PRIMARY KEY``, ``odcs_json TEXT NOT NULL``.
    """

    def __init__(self, pool):  # type: ignore[no-untyped-def]
        self._pool = pool

    async def _ensure_schema(self) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS vlas (
                    id         UUID PRIMARY KEY,
                    odcs_json  TEXT NOT NULL
                )
                """
            )

    async def all(self) -> list[dict[str, Any]]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("SELECT id, odcs_json FROM vlas")
        return [_with_id(r["odcs_json"], r["id"]) for r in rows]

    async def by_id(self, id: UUID) -> Optional[dict[str, Any]]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, odcs_json FROM vlas WHERE id = $1", id
            )
        return _with_id(row["odcs_json"], row["id"]) if row is not None else None

    async def add(self, vla: dict[str, Any]) -> Optional[UUID]:
        id = uuid4()
        vla = {k: v for k, v in vla.items() if k != "id"}
        async with self._pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO vlas (id, odcs_json) VALUES ($1, $2)",
                id,
                json.dumps(vla),
            )
        return id

    async def remove_all(self) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute("DELETE FROM vlas")