"""Pydantic v2 schemas accepted/returned by the VLA Manager API.

These mirror the Kotlin DTOs byte-for-byte so the existing VLA Manager
Vue UI and consumers of the prior ``dva-api /vla`` routes interoperate
without contract changes.

Reference:
- model/src/main/kotlin/hu/bme/mit/ftsrg/dva/vla/VLANew.kt
- model/src/main/kotlin/hu/bme/mit/ftsrg/odcs/DataQuality.kt
- model/src/main/kotlin/hu/bme/mit/ftsrg/dva/dto/IDDTO.kt
- model/src/main/kotlin/hu/bme/mit/ftsrg/dva/dto/ErrDTO.kt
"""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class DataQuality(BaseModel):
    """A single quality requirement (ODCS DataQuality fragment)."""

    engine: str
    implementation: str


class VLANew(BaseModel):
    """Body of ``POST /vla``. All fields optional — partial ODCS payload.

    The ``schema`` field is renamed via alias because ``schema`` is a
    reserved attribute name on pydantic BaseModel. Inputs and outputs
    use the JSON key ``schema`` transparently.
    """

    model_config = ConfigDict(populate_by_name=True)

    description: Optional[str] = None
    servers: Optional[list[Any]] = None
    schema_: Optional[dict[str, Any]] = Field(default=None, alias="schema")
    quality: Optional[list[DataQuality]] = None
    price: Optional[dict[str, Any]] = None
    team: Optional[list[Any]] = None
    roles: Optional[list[Any]] = None
    slaProperties: Optional[list[Any]] = None
    support: Optional[list[Any]] = None
    tags: Optional[list[Any]] = None


class IDDTO(BaseModel):
    id: UUID


class TemplateInstantiation(BaseModel):
    """One entry in ``VLANewFromTemplates.qualityTemplates`` — a template
    id plus the model dict to render it with."""

    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    model: dict[str, Any]


class VLANewFromTemplates(VLANew):
    """Body of ``POST /vla/from-templates``. Extends VLANew with a
    ``qualityTemplates`` array whose entries are rendered and merged
    into the VLA's ``quality`` array before persistence."""

    model_config = ConfigDict(populate_by_name=True)

    quality_templates: list[TemplateInstantiation] = Field(
        alias="qualityTemplates", default_factory=list
    )


class ErrDTO(BaseModel):
    type: str
    title: str


# ---------------------------------------------------------------------------
# Template models — ported from the deleted Kotlin ``Template.kt`` (commit
# ba876ff~1). Wire format is camelCase to remain byte-compatible with the
# existing VLA Manager Vue UI and the OpenAPI spec.
# ---------------------------------------------------------------------------

class EvaluationMethod(BaseModel):
    """Renderable evaluation method inside a Template."""

    model_config = ConfigDict(populate_by_name=True)

    engine: str
    variable_schema: dict[str, Any] = Field(alias="variableSchema")
    implementation_template: str = Field(alias="implementationTemplate")


class TemplateNew(BaseModel):
    """Body of ``POST /template`` — create a new template (no id)."""

    model_config = ConfigDict(populate_by_name=True)

    name: str
    description: Optional[str] = None
    criterion_type: str = Field(alias="criterionType")
    target_aspect: str = Field(alias="targetAspect")
    evaluation_method: EvaluationMethod = Field(alias="evaluationMethod")


class TemplatePatch(BaseModel):
    """Body of ``PATCH /template/{id}`` — partial update. ``id`` must
    match the path parameter."""

    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    name: Optional[str] = None
    description: Optional[str] = None
    criterion_type: Optional[str] = Field(default=None, alias="criterionType")
    target_aspect: Optional[str] = Field(default=None, alias="targetAspect")
    evaluation_method: Optional[EvaluationMethod] = Field(
        default=None, alias="evaluationMethod"
    )


class Template(BaseModel):
    """Full template representation returned by GET endpoints."""

    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    name: str
    description: Optional[str] = None
    criterion_type: str = Field(alias="criterionType")
    target_aspect: str = Field(alias="targetAspect")
    evaluation_method: EvaluationMethod = Field(alias="evaluationMethod")