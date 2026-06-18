from datetime import datetime
from enum import StrEnum, auto
from typing import Any, Optional

from pydantic import BaseModel, field_validator


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


class EvaluationResult(BaseModel):
    engine: Optional[QualityEngine]
    timestamp: datetime
    success: bool
    details: Optional[str] = None
    error: Optional[str] = None


class AoVRequest(BaseModel):
    id: str
    exchangeID: str
    contract: dict[str, Any]
    data: Any
    attesterID: str


class AoVGenerationRequestPayload(BaseModel):
    success: bool
    results: list[EvaluationResult]


class AoVGenerationRequest(BaseModel):
    request_id: str
    exchange_id: str
    contract_id: str
    subject: str
    issuer_id: str
    payload: AoVGenerationRequestPayload
    target: str


class JQResult(BaseModel):
    success: bool
    details: str


class JSONSchemaValidationResult(BaseModel):
    success: bool
    errors: Optional[str] = None


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
