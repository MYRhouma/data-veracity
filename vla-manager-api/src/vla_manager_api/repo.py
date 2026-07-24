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
from typing import Any, Optional, Protocol, Sequence
from uuid import UUID, uuid4

__all__ = ["VLARepo", "FakeVLARepo", "PgVLARepo",
           "TemplateRepo", "FakeTemplateRepo", "PgTemplateRepo",
           "render_template"]


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


# ---------------------------------------------------------------------------
# Template repository — ported from deleted Kotlin ``PgTemplateRepo.kt``
# (commit ba876ff~1). Owns two tables: ``templates`` + ``evaluation_methods``
# (1:1). The render helper uses Handlebars-compatible ``{{var}}`` syntax via
# the ``chevron`` package, byte-compatible with the old Kotlin Handlebars
# output.
# ---------------------------------------------------------------------------


def render_template(implementation_template: str, model: dict[str, Any]) -> str:
    """Render a Handlebars ``{{var}}`` template string with a model dict.

    Mirrors the deleted Kotlin ``Template.render`` (service/templates.kt).
    Uses the ``chevron`` library for Mustache/Handlebars fidelity.
    """
    import chevron

    return chevron.render(implementation_template, model)


class TemplateRepo(Protocol):
    """Minimal contract for Template persistence."""

    async def all(self) -> list[dict[str, Any]]: ...

    async def by_id(self, id: UUID) -> Optional[dict[str, Any]]: ...

    async def add(self, template: dict[str, Any]) -> Optional[UUID]: ...

    async def update(self, id: UUID, patch: dict[str, Any]) -> Optional[dict[str, Any]]: ...

    async def remove(self, id: UUID) -> bool: ...

    async def remove_all(self) -> None: ...


class FakeTemplateRepo:
    """In-memory Template repository for tests."""

    def __init__(self) -> None:
        self._templates: dict[UUID, dict[str, Any]] = {}

    async def all(self) -> list[dict[str, Any]]:
        # Inject id into returned dict (mirror PgTemplateRepo behaviour)
        return [{**t, "id": str(tid)} for tid, t in self._templates.items()]

    async def by_id(self, id: UUID) -> Optional[dict[str, Any]]:
        t = self._templates.get(id)
        return {**t, "id": str(id)} if t is not None else None

    async def add(self, template: dict[str, Any]) -> Optional[UUID]:
        id = uuid4()
        stored = {k: v for k, v in template.items() if k != "id"}
        self._templates[id] = stored
        return id

    async def update(self, id: UUID, patch: dict[str, Any]) -> Optional[dict[str, Any]]:
        existing = self._templates.get(id)
        if existing is None:
            return None
        for k, v in patch.items():
            if v is not None:
                existing[k] = v
        return {**existing, "id": str(id)}

    async def remove(self, id: UUID) -> bool:
        return self._templates.pop(id, None) is not None

    async def remove_all(self) -> None:
        self._templates.clear()


class PgTemplateRepo:
    """Async-backed PostgreSQL Template repository using asyncpg.

    Owns the ``templates`` + ``evaluation_methods`` tables (1:1).
    Columns mirror the deleted Kotlin ``templateMapping.kt``.
    """

    def __init__(self, pool):  # type: ignore[no-untyped-def]
        self._pool = pool

    async def _ensure_schema(self) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evaluation_methods (
                    id                     UUID PRIMARY KEY,
                    engine                 VARCHAR(255) NOT NULL,
                    variable_schema        TEXT NOT NULL,
                    implementation_template TEXT NOT NULL
                )
                """
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS templates (
                    id                  UUID PRIMARY KEY,
                    name                VARCHAR(255) NOT NULL,
                    description         TEXT,
                    criterion_type      VARCHAR(255) NOT NULL,
                    target_aspect       VARCHAR(255) NOT NULL,
                    evaluation_method_id UUID NOT NULL
                        REFERENCES evaluation_methods(id) ON DELETE CASCADE
                )
                """
            )

    def _row_to_dict(self, row) -> dict[str, Any]:  # type: ignore[no-untyped-def]
        return {
            "id": str(row["id"]),
            "name": row["name"],
            "description": row["description"],
            "criterionType": row["criterion_type"],
            "targetAspect": row["target_aspect"],
            "evaluationMethod": {
                "engine": row["engine"],
                "variableSchema": json.loads(row["variable_schema"]),
                "implementationTemplate": row["implementation_template"],
            },
        }

    async def all(self) -> list[dict[str, Any]]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT t.id, t.name, t.description, t.criterion_type,
                       t.target_aspect, em.engine, em.variable_schema,
                       em.implementation_template
                FROM templates t
                JOIN evaluation_methods em ON t.evaluation_method_id = em.id
                """
            )
        return [self._row_to_dict(r) for r in rows]

    async def by_id(self, id: UUID) -> Optional[dict[str, Any]]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT t.id, t.name, t.description, t.criterion_type,
                       t.target_aspect, em.engine, em.variable_schema,
                       em.implementation_template
                FROM templates t
                JOIN evaluation_methods em ON t.evaluation_method_id = em.id
                WHERE t.id = $1
                """,
                id,
            )
        return self._row_to_dict(row) if row is not None else None

    async def add(self, template: dict[str, Any]) -> Optional[UUID]:
        em = template["evaluationMethod"]
        em_id = uuid4()
        t_id = uuid4()
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO evaluation_methods (id, engine, variable_schema, implementation_template)
                VALUES ($1, $2, $3, $4)
                """,
                em_id,
                em["engine"],
                json.dumps(em["variableSchema"]),
                em["implementationTemplate"],
            )
            await conn.execute(
                """
                INSERT INTO templates (id, name, description, criterion_type, target_aspect, evaluation_method_id)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                t_id,
                template["name"],
                template.get("description"),
                template["criterionType"],
                template["targetAspect"],
                em_id,
            )
        return t_id

    async def update(self, id: UUID, patch: dict[str, Any]) -> Optional[dict[str, Any]]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT evaluation_method_id FROM templates WHERE id = $1", id
            )
            if row is None:
                return None
            em_id = row["evaluation_method_id"]
            if patch.get("name") is not None:
                await conn.execute("UPDATE templates SET name = $2 WHERE id = $1", id, patch["name"])
            if patch.get("description") is not None:
                await conn.execute("UPDATE templates SET description = $2 WHERE id = $1", id, patch["description"])
            if patch.get("criterionType") is not None:
                await conn.execute("UPDATE templates SET criterion_type = $2 WHERE id = $1", id, patch["criterionType"])
            if patch.get("targetAspect") is not None:
                await conn.execute("UPDATE templates SET target_aspect = $2 WHERE id = $1", id, patch["targetAspect"])
            em_patch = patch.get("evaluationMethod")
            if em_patch is not None:
                await conn.execute(
                    "UPDATE evaluation_methods SET engine = $2 WHERE id = $1",
                    em_id, em_patch["engine"],
                )
                await conn.execute(
                    "UPDATE evaluation_methods SET variable_schema = $2 WHERE id = $1",
                    em_id, json.dumps(em_patch["variableSchema"]),
                )
                await conn.execute(
                    "UPDATE evaluation_methods SET implementation_template = $2 WHERE id = $1",
                    em_id, em_patch["implementationTemplate"],
                )
        return await self.by_id(id)

    async def remove(self, id: UUID) -> bool:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT evaluation_method_id FROM templates WHERE id = $1", id
            )
            if row is None:
                return False
            em_id = row["evaluation_method_id"]
            await conn.execute("DELETE FROM templates WHERE id = $1", id)
            await conn.execute("DELETE FROM evaluation_methods WHERE id = $1", em_id)
        return True

    async def remove_all(self) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute("DELETE FROM templates")
            await conn.execute("DELETE FROM evaluation_methods")