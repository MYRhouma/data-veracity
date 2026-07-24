"""FastAPI routes for the VLA Manager API.

VLA CRUD routes plus POST /vla/from-templates which fetches VLA
templates, renders each with a model, and merges the rendered quality
requirements into the VLA before persistence.

DELETE /vla is guarded by :func:`.auth.require_api_key`.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from .auth import require_api_key
from .dependencies import get_repo, get_template_repo
from .models import ErrDTO, IDDTO, VLANew, VLANewFromTemplates
from .repo import TemplateRepo, VLARepo, render_template


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


@router.post("/vla/from-templates", status_code=status.HTTP_201_CREATED, response_model=IDDTO)
async def create_vla_from_templates(
    vla_req: VLANewFromTemplates,
    repo: VLARepo = Depends(get_repo),
    template_repo: TemplateRepo = Depends(get_template_repo),
) -> IDDTO:
    base_vla = _wrap_vla(vla_req)

    rendered_quality: list[dict[str, Any]] = []
    for qt in vla_req.quality_templates:
        template = await template_repo.by_id(qt.id)
        if template is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        em = template["evaluationMethod"]
        try:
            implementation = render_template(em["implementationTemplate"], qt.model)
        except Exception:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail=ErrDTO(
                    type="BAD_REQUEST",
                    title=f"Failed to render template {qt.id}",
                ).model_dump(),
            )
        rendered_quality.append(
            {"engine": em["engine"], "implementation": implementation}
        )

    existing_quality = base_vla.get("quality") or []
    base_vla["quality"] = list(existing_quality) + rendered_quality

    new_id = await repo.add(base_vla)
    if new_id is None:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrDTO(type="UNKNOWN", title="Failed to create VLA").model_dump(),
        )
    return IDDTO(id=new_id)


@router.delete("/vla", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_vlas(
    _: None = Depends(require_api_key), repo: VLARepo = Depends(get_repo)
) -> None:
    await repo.remove_all()
    return None