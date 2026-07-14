"""FastAPI routes for VLA Template CRUD.

Ported from the deleted Kotlin ``templateRoutes.kt`` (commit ba876ff~1).
Seven routes — byte-compatible with the old dva-api contract:

* ``GET    /template``          — list all templates
* ``POST   /template``          — create a template
* ``GET    /template/{id}``     — fetch a template by id
* ``PATCH  /template/{id}``     — partial update (id in body must match path)
* ``DELETE /template/{id}``     — delete one template
* ``DELETE /template``          — delete all (dev, API-key guarded)
* ``POST   /template/{id}/render`` — render the Handlebars template with a model
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from .auth import require_api_key
from .dependencies import get_template_repo
from .models import ErrDTO, IDDTO, Template, TemplateNew, TemplatePatch
from .repo import TemplateRepo, render_template


router = APIRouter()


class RenderResult(BaseModel):
    """Result of rendering a template — a single DataQuality fragment."""

    engine: str
    implementation: str


@router.get("/template", response_model=list[Template])
async def list_templates(repo: TemplateRepo = Depends(get_template_repo)) -> list[dict[str, Any]]:
    return await repo.all()


@router.post("/template", status_code=status.HTTP_201_CREATED, response_model=IDDTO)
async def create_template(
    template_req: TemplateNew, repo: TemplateRepo = Depends(get_template_repo)
) -> IDDTO:
    template = template_req.model_dump(by_alias=True, exclude_none=True)
    new_id = await repo.add(template)
    if new_id is None:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrDTO(type="UNKNOWN", title="Failed to create template").model_dump(),
        )
    return IDDTO(id=new_id)


@router.get("/template/{id}", response_model=Template)
async def get_template(id: UUID, repo: TemplateRepo = Depends(get_template_repo)) -> dict[str, Any]:
    template = await repo.by_id(id)
    if template is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return template


@router.patch("/template/{id}", response_model=Template)
async def update_template(
    id: UUID,
    patch: TemplatePatch,
    repo: TemplateRepo = Depends(get_template_repo),
) -> dict[str, Any]:
    if id != patch.id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=ErrDTO(
                type="BAD_REQUEST",
                title="ID path parameter does not match ID in body",
            ).model_dump(),
        )
    patch_dict = patch.model_dump(by_alias=True, exclude_none=True)
    updated = await repo.update(id, patch_dict)
    if updated is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return updated


@router.delete("/template/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(id: UUID, repo: TemplateRepo = Depends(get_template_repo)) -> None:
    if not await repo.remove(id):
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return None


@router.delete("/template", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_templates(
    _: None = Depends(require_api_key),
    repo: TemplateRepo = Depends(get_template_repo),
) -> None:
    await repo.remove_all()
    return None


@router.post("/template/{id}/render", response_model=RenderResult)
async def render_template_route(
    id: UUID,
    model: dict[str, Any],
    repo: TemplateRepo = Depends(get_template_repo),
) -> RenderResult:
    template = await repo.by_id(id)
    if template is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    em = template["evaluationMethod"]
    try:
        rendered = render_template(em["implementationTemplate"], model)
    except Exception:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=ErrDTO(type="BAD_REQUEST", title="Failed to render template").model_dump(),
        )
    return RenderResult(engine=em["engine"], implementation=rendered)