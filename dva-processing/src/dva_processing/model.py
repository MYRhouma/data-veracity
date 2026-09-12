from datetime import datetime
from enum import StrEnum, auto
from typing import Any, Optional

from open_data_contract_standard.model import DataQuality
from pydantic import BaseModel, field_validator


class CapitalStrEnum(StrEnum):
    @staticmethod
    def _generate_next_value_(name, *args):
        return name.upper()


class QualityEngine(CapitalStrEnum):
    schema = auto()
    great_expectations = auto()
    jq = auto()


class EvaluationRequest(BaseModel):
    # ODCS types `engine` as a free-form string, so an unusable engine is
    # only rejected once `eval.eval_requirement` gets to it.
    requirement: DataQuality
    data: Any


class EvaluationResult(BaseModel):
    # An EvaluationResult only exists once an engine has run, so the engine
    # is always known – see `./components.yaml#/schemas/EvaluationResult`.
    engine: QualityEngine
    timestamp: datetime
    success: bool
    details: Optional[str] = None
    error: Optional[str] = None


class ErrDTO(BaseModel):
    """Problem detail returned on error responses (spec ``Error``)."""

    type: str
    title: str
    detail: Optional[str] = None


class JQResult(BaseModel):
    success: bool
    details: str


class JSONSchemaValidationResult(BaseModel):
    success: bool
    # Rendered from the jsonschema ValidationError; absent when the data
    # conforms.
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
