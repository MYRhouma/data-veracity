"""FastAPI routes for the DVA VC Manager.

Two AoV endpoints called by the DVA API during the synchronous
attestation flow:

* ``POST /aov/issue`` — called by the DVA API during credential
  issuance with the seven claims + the veracity-check results array.
  Generates a UUID for the credential, signs the JWS, and returns
  only the compact JWS string (issuer did:key, vc_id, and issuance
  date are all encoded in the JWS itself).
* ``POST /aov/verify`` — called by the DVA API at the consumer side to
  verify a JWS. The issuer ``did:key`` is extracted from the JWS
  payload and looked up in the whitelist. Fail-closed: rejects if the
  whitelist is empty or the issuer is not registered.

Plus four admin endpoints (all bearer-auth-guarded):

* ``GET /admin/whitelist`` — list trusted attesters.
* ``POST /admin/whitelist`` — register a trusted attester's did:key.
* ``DELETE /admin/whitelist/{did_key}`` — remove an attester.
* ``GET /admin/keys`` — view this service's own issuer did:key
  (read-only; no private key bytes exposed).
"""

from __future__ import annotations

import urllib.parse
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from .auth import require_api_key
from .dependencies import get_whitelist
from .did_key import did_key_to_public_key
from .keys import SigningKeyStore
from .models import (
    AovIssueRequest,
    AovIssueResponse,
    AovVerifyRequest,
    AovVerifyResponse,
    OwnKeyDTO,
    WhitelistAddRequest,
    WhitelistEntryDTO,
)
from .signing import AovClaims, decode_payload, sign_jws, verify_jws
from .whitelist import WhitelistRepo

router = APIRouter()


def _get_key_store() -> SigningKeyStore:
    """Lazily construct the app-wide signing key store.

    Resolved via FastAPI's dependency system in tests via
    ``app.dependency_overrides`` so the test suite can swap in a
    key store at a temp-file path.
    """
    from .config import cfg

    return SigningKeyStore(cfg.signing_key_path)


@router.post("/aov/issue", response_model=AovIssueResponse)
async def aov_issue(req: AovIssueRequest) -> AovIssueResponse:
    """Issue an AoV JWS credential from the veracity-check results."""
    key_store = _get_key_store()
    keypair = key_store.load_or_generate()
    issuer_did_key = key_store.issuer_did_key()

    # Mapped to the camelCase AovClaims fields — AovClaims VC-subject
    # JSON keys must stay byte-identical with the Kotlin issuer, so
    # we hand the model the snake_case values and rely on the field
    # aliases in build_aov_payload.
    claims = AovClaims(
        vc_id=str(uuid4()),
        valid_since=req.valid_since,
        subject=req.subject,
        issuer_id=req.issuer_id,
        record_id=req.record_id,
        contract_id=req.contract_id,
        data_exchange_id=req.data_exchange_id,
        payload=req.payload,
    )
    jws = sign_jws(claims, keypair.private, issuer_did_key)
    return AovIssueResponse(jws=jws)


@router.post("/aov/verify", response_model=AovVerifyResponse)
async def aov_verify(
    req: AovVerifyRequest,
    whitelist: WhitelistRepo = Depends(get_whitelist),
) -> AovVerifyResponse:
    """Verify an AoV JWS. The issuer did:key is extracted from the JWS
    payload and looked up in the whitelist. Fail-closed."""

    # 1. Decode the JWS payload to extract the issuer did:key.
    try:
        payload = decode_payload(req.jws)
    except Exception as e:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"malformed JWS: {e}",
        )

    issuer_did_key = payload.get("issuer")
    if not issuer_did_key:
        return AovVerifyResponse(verified=False, reason="JWS payload missing issuer")

    # 2. Whitelist must be non-empty.
    entries = await whitelist.all()
    if not entries:
        return AovVerifyResponse(
            verified=False,
            reason="whitelist is not configured; verification is disabled",
        )

    # 3. Issuer must be whitelisted — fail-closed when not found.
    entry = await whitelist.find(issuer_did_key)
    if entry is None:
        return AovVerifyResponse(verified=False, reason="issuer not whitelisted")

    # 4. Derive the public key from the whitelist record's did:key.
    try:
        public_key = did_key_to_public_key(entry.did_key)
    except Exception as e:
        return AovVerifyResponse(
            verified=False,
            reason=f"whitelist entry contains invalid did:key: {e}",
        )

    # 5. Verify the Ed25519 signature.
    from nacl.signing import VerifyKey

    try:
        ok = verify_jws(req.jws, VerifyKey(bytes(public_key)))
    except Exception as e:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"malformed JWS: {e}",
        )

    if not ok:
        return AovVerifyResponse(verified=False, reason="signature mismatch")

    return AovVerifyResponse(verified=True)


# --- Admin ------------------------------------------------------------


admin_router = APIRouter()


@admin_router.get("/admin/whitelist", response_model=list[WhitelistEntryDTO])
async def whitelist_list(
    _: None = Depends(require_api_key),
    whitelist: WhitelistRepo = Depends(get_whitelist),
) -> list[WhitelistEntryDTO]:
    entries = await whitelist.all()
    return [WhitelistEntryDTO(id=e.id, did_key=e.did_key, label=e.label) for e in entries]


@admin_router.post(
    "/admin/whitelist",
    status_code=status.HTTP_201_CREATED,
    response_model=WhitelistEntryDTO,
)
async def whitelist_add(
    req: WhitelistAddRequest,
    _: None = Depends(require_api_key),
    whitelist: WhitelistRepo = Depends(get_whitelist),
) -> WhitelistEntryDTO:
    entry = await whitelist.add(req.did_key, req.label)
    return WhitelistEntryDTO(id=entry.id, did_key=entry.did_key, label=entry.label)


@admin_router.delete("/admin/whitelist/{did_key}", status_code=status.HTTP_204_NO_CONTENT)
async def whitelist_remove(
    did_key: str,
    _: None = Depends(require_api_key),
    whitelist: WhitelistRepo = Depends(get_whitelist),
) -> None:
    # URL-decode in case the path contains special chars (did:key contains ':').
    decoded = urllib.parse.unquote(did_key)
    removed = await whitelist.remove(decoded)
    if not removed:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "did:key not in whitelist")
    return None


@admin_router.get("/admin/keys", response_model=OwnKeyDTO)
async def keys_view(_: None = Depends(require_api_key)) -> OwnKeyDTO:
    from .config import cfg

    key_store = SigningKeyStore(cfg.signing_key_path)
    key_store.load_or_generate()
    return OwnKeyDTO(issuer_did_key=key_store.issuer_did_key(), key_path=cfg.signing_key_path)