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

from pydantic import BaseModel, ConfigDict, Field


# JSON keys for these request/response models are byte-identical with the
# Kotlin ``dva-api`` DTOs (``route/aovRoutes.kt:39-57`` and
# ``AoVDTOs.kt``). Kotlin property names are ``camelCase`` (e.g. ``vcId``,
# ``issuerDidKey``); pydantic's Python-native attribute names stay
# ``snake_case`` but the wire format MUST be ``camelCase`` so the Kotlin
# client/server round-trip works without contract drift. We add aliases
# to each advanced-name field and let ``populate_by_name=True`` keep
# snake_case accepted on the Python side (for unit tests and direct
# curl).
_CAMEL = ConfigDict(populate_by_name=True)


class EvaluationResultDTO(BaseModel):
    """One row of the veracity-check results array.

    Field names are single words so no aliasing is needed — they are
    already byte-identical with the Kotlin ``EvaluationResultDTO``.
    """

    engine: Optional[str] = None
    timestamp: datetime
    success: bool
    details: Optional[str] = None
    error: Optional[str] = None


class AovIssueRequest(BaseModel):
    """Body of ``POST /aov/issue``.

    The DVA API posts the eight claims fields and the veracity-check
    results array. The VC Manager decides whether to issue based on
    ``all_success`` (computed here) and generates a fresh UUID for
    the credential.
    """

    model_config = _CAMEL

    valid_since: str = Field(..., alias="validSince")
    subject: str
    issuer_id: str = Field(..., alias="issuerId")
    record_id: str = Field(..., alias="recordId")
    contract_id: str = Field(..., alias="contractId")
    data_exchange_id: str = Field(..., alias="dataExchangeId")
    payload: str
    evaluation_results: list[EvaluationResultDTO] = Field(
        ..., alias="evaluationResults"
    )


class AovIssueResponse(BaseModel):
    """Returned by ``POST /aov/issue``. The JWS contains the issuer
    ``did:key``, the VC UUID, and the issuance timestamp, so they are
    not duplicated in the response body.
    """

    model_config = _CAMEL

    jws: str


class AovVerifyRequest(BaseModel):
    """Body of ``POST /aov/verify``. Only the compact JWS string is
    supplied; the issuer ``did:key`` is extracted from the JWS payload.
    """

    model_config = _CAMEL

    jws: str


class AovVerifyResponse(BaseModel):
    """Returned by ``POST /aov/verify``."""

    verified: bool
    reason: Optional[str] = None


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