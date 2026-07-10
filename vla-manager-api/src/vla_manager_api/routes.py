"""FastAPI routes for the VLA Manager API.

Mirrors, byte-for-byte, the Kotlin ``dva-api`` VLA routes at
``route/vlaRoutes.kt`` (lines 36-147). Differences:

* No ``POST /vla/from-templates`` yet — templates are reserved for a
  later refactor iteration along with the ``/evaluate/from-template`` proxy.
  Returns ``501 Not Implemented`` in the interim so the VLA Manager
  UI surfaces the missing functionality rather than failing silently.
* ``DELETE /vla`` is guarded by :func:`.auth.require_api_key`.

The ``GET`` endpoints inject the ``id`` field into each returned object
on read (mirrors ``VLAEntity.toModel()`` at ``vlaMapping.kt:22-23``).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from .auth import require_api_key
from .dependencies import get_repo
from .models import ErrDTO, IDDTO, VLANew
from .repo import VLARepo


router = APIRouter()


def _wrap_vla(vla_req: VLANew) -> dict[str, Any]:
    """Wrap a partial ODCS payload with the boilerplate headers, mirroring
    the Kotlin ``buildJsonObject`` wrapper at ``vlaRoutes.kt:50-67``."""
    base: dict[str, Any] = {
        "apiVersion": "v3.0.2",
        "kind": "DataContract",
        "version": "0.1.0",
        "status": "active",
    }
    data = vla_req.model_dump(exclude_none=True, by_alias=True)
    base.update(data)
    return base


@router.get("/vla")
async def list_vlas(repo: VLARepo = Depends(get_repo)) -> list[dict[str, Any]]:
    return await repo.all()


@router.get("/vla/{id}")
async def get_vla(id: UUID, repo: VLARepo = Depends(get_repo)) -> dict[str, Any]:
    vla = await repo.by_id(id)
    if vla is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return vla


@router.post("/vla", status_code=status.HTTP_201_CREATED, response_model=IDDTO)
async def create_vla(vla_req: VLANew, repo: VLARepo = Depends(get_repo)) -> IDDTO:
    vla = _wrap_vla(vla_req)
    new_id = await repo.add(vla)
    if new_id is None:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrDTO(type="UNKNOWN", title="Failed to create VLA").model_dump(),
        )
    return IDDTO(id=new_id)


@router.post("/vla/from-templates", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def create_vla_from_templates() -> dict[str, str]:
    """Reserved — implemented in a later step alongside the
    ``/api/evaluate/from-template`` Data-Intermediary-only proxy."""
    return {"detail": "POST /vla/from-templates is not implemented yet"}


@router.delete("/vla", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_vlas(
    _: None = Depends(require_api_key), repo: VLARepo = Depends(get_repo)
) -> None:
    await repo.remove_all()
    return None