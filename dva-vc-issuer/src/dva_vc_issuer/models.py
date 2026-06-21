from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class AoVRequest(BaseModel):
    request_id: str
    exchange_id: str
    contract_id: str
    subject: str
    issuer_id: str
    payload: dict[str, Any]
    target: str = "self"


class EvaluationResultPayload(BaseModel):
    success: bool
    results: list[dict[str, Any]]


class TrancheFieldResult(BaseModel):
    name: str
    mandatory: bool
    passed: bool


class TrancheEvaluation(BaseModel):
    tranche_level: str = "incomplete"
    percentage: int = 0
    mandatory_passed: list[str] = Field(default_factory=list)
    mandatory_failed: list[str] = Field(default_factory=list)
    optional_passed: list[str] = Field(default_factory=list)
    optional_failed: list[str] = Field(default_factory=list)
    total_passed: int = 0
    total_failed: int = 0
    field_results: list[TrancheFieldResult] = Field(default_factory=list)


class VerifiableCredential(BaseModel):
    context: list[str] = Field(
        default_factory=lambda: [
            "https://www.w3.org/ns/credentials/v2",
        ],
        alias="@context",
    )
    id: str
    type: list[str] = Field(
        default_factory=lambda: ["VerifiableCredential", "AttestationOfVeracity"]
    )
    issuer: str
    valid_from: datetime
    credential_subject: dict[str, Any]
    proof: Optional[dict[str, Any]] = None


class GenerateAoVResponse(BaseModel):
    message: str
    vc: dict[str, Any]


class VerifyRequest(BaseModel):
    vc: dict[str, Any]


class VerifyResponse(BaseModel):
    valid: bool
    error: Optional[str] = None