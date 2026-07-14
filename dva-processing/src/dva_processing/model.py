from datetime import datetime
from enum import StrEnum, auto
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CapitalStrEnum(StrEnum):
    @staticmethod
    def _generate_next_value_(name, *args):
        return name.upper()


class QualityEngine(CapitalStrEnum):
    schema = auto()
    great_expectations = auto()
    jq = auto()


class Requirement(BaseModel):
    implementation: str
    engine: QualityEngine


class EvaluationRequest(BaseModel):
    requirement: Requirement
    data: Any


class EvaluateBatchRequest(BaseModel):
    """Body of ``POST /evaluate-batch``.

    The DVA API posts the full VLA document (as retrieved from the VLA
    Manager API) and the original data. The processing service iterates
    over ``vla.schema[*].quality[*]`` and returns one
    :class:`EvaluationResult` per requirement — the "array of (requirement,
    result) pairs" produced by veracity checks in the synchronous
    attestation flow.
    """

    vla: dict[str, Any]
    data: Any


class EvaluationResult(BaseModel):
    engine: Optional[QualityEngine]
    timestamp: datetime
    success: bool
    details: Optional[str] = None
    error: Optional[str] = None


class EvaluationFromTemplateRequest(BaseModel):
    """Body of ``POST /evaluate/from-template``.

    Data-Intermediary-only endpoint used while authoring VLAs. The caller
    supplies a template ID + the model values to render the template into
    a concrete ``DataQuality`` requirement, then evaluates against ``data``.
    Mirrors the deleted Kotlin ``EvaluateFromTemplate`` (commit ba876ff~1).
    Field names are camelCase on the wire to match the Kotlin contract.
    """

    model_config = ConfigDict(populate_by_name=True)

    template_id: Any = Field(alias="templateID")
    template_model: dict[str, Any] = Field(alias="templateModel")
    data: Any


class JQResult(BaseModel):
    success: bool
    details: str


class JSONSchemaValidationResult(BaseModel):
    success: bool
    errors: str


class JSONToDFSchemaColumnSpec(BaseModel):
    jsonpath: str
    dtype: str = "string"


class JSONToDFSchema(BaseModel):
    root_path: str = "$"
    columns: dict[str, JSONToDFSchemaColumnSpec] = {}

    @field_validator("columns", mode="before")
    @classmethod
    def add_default_colspec(cls, v):
        if isinstance(v, dict):
            result = {}
            for key, val in v.items():
                if val is None:
                    val = {}
                if isinstance(val, dict):
                    val.setdefault("jsonpath", f"$.{key}")
                result[key] = val
            return result
        return v


class GreatExpectationsMeta(BaseModel):
    schema: JSONToDFSchema = JSONToDFSchema()


class GreatExpectationParams(BaseModel):
    type: str
    kwargs: dict[str, Any]
    meta: GreatExpectationsMeta = GreatExpectationsMeta()
