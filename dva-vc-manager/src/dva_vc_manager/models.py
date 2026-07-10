"""HTTP request/response models for /aov/issue and /aov/verify.

The JSON shape is kept byte-compatible with the Kotlin ``dva-api``
``/attestation`` response so the PDC client
(``dataspace-connector-1.10.2/src/libs/third-party/dva.ts``) sees no
contract change when the JWS is issued by this Python service instead
of the inlined Kotlin signer.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel


class EvaluationResultDTO(BaseModel):
    """One row of the veracity-check results array."""

    engine: Optional[str] = None
    timestamp: datetime
    success: bool
    details: Optional[str] = None
    error: Optional[str] = None


class AovIssueRequest(BaseModel):
    """Body of ``POST /aov/issue``.

    The DVA API posts the eight claims fields and the veracity-check
    results array. The VC Manager decides whether to issue based on
    ``all_success`` (computed here) — but the DVA API also pre-computes
    this and renders the appropriate response either way.
    """

    vc_id: UUID
    valid_since: str
    subject: str
    issuer_id: str
    record_id: str
    contract_id: str
    data_exchange_id: str
    payload: str
    evaluation_results: list[EvaluationResultDTO]

    model_config = {"populate_by_name": True}


class AovIssueResponse(BaseModel):
    """Returned by ``POST /aov/issue`` and merged into the DVA API's
    ``AoVResponseDTO`` verbatim.
    """

    jws: str
    vc_id: UUID
    issuer_did_key: str
    vc_issued_date: str


class AovVerifyRequest(BaseModel):
    """Body of ``POST /aov/verify`` — matches the Kotlin
    ``AttestationVerifySyncRequestDTO`` exactly.
    """

    jws: str
    attester_did_key: str

    model_config = {"populate_by_name": True}


class AovVerifyResponse(BaseModel):
    """Returned by ``POST /aov/verify`` — matches the Kotlin
    ``AttestationVerifySyncResponseDTO`` exactly.
    """

    verified: bool
    reason: Optional[str] = None
    payload: Optional[dict[str, Any]] = None


class WhitelistAddRequest(BaseModel):
    """Body of ``POST /admin/whitelist``."""

    did_key: str
    label: Optional[str] = None


class WhitelistEntryDTO(BaseModel):
    """Returned by ``GET /admin/whitelist`` and ``POST /admin/whitelist``."""

    id: UUID
    did_key: str
    label: Optional[str] = None


class OwnKeyDTO(BaseModel):
    """Returned by ``GET /admin/keys`` — read-only view of this
    service's signing ``did:key`` (no private bytes).
    """

    issuer_did_key: str
    key_path: str