"""JWS issuance and verification.

Muliberates the production of a compact JWS (``header.payload.signature``)
over a W3C VC 2.0 JSON-LD payload. The signed JSON shape is
**byte-for-byte identical** to the Kotlin ``JwsSigner.kt:39-57`` so any
existing consumer of an AoV JWS (PDC, other DVAs, downstream wallets)
can verify a Python-issued credential with the Kotlin verifier and
vice-versa.

The cryptography itself is delegated entirely to PyNaCl (libsodium):

* :func:`nacl.signing.SigningKey.sign` for EdDSA signatures.
* :func:`nacl.signing.VerifyKey.verify` for EdDSA verification.

No hand-rolled cryptography anywhere. Only the JSON shape construction,
base64url encoding, and the standard JWS compact serialization
concatenation happen here.
"""

from __future__ import annotations

import base64
import json
from typing import Any

from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey

from .did_key import did_key_to_public_key

# JWS header constants — must match Kotlin ``JwsSigner.kt:30-34`` exactly.
JWS_HEADER_ALG = "EdDSA"
JWS_HEADER_TYPE = "VC+LD-JSON+JWS"
VC_CONTEXT = "https://www.w3.org/2018/credentials/v1"
VC_TYPE = "VerifiableCredential"
AOV_TYPE = "AttestationOfVeracity"


def _b64url(data: bytes) -> str:
    """Standard JWS base64url **without** padding (per RFC 7515 §2.2.2)."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(segment: str) -> bytes:
    """Inverse of :func:`_b64url` — re-adds padding before decoding."""
    pad = (-len(segment)) % 4
    return base64.urlsafe_b64decode(segment + "=" * pad)


def _json_compact(obj: dict[str, Any]) -> bytes:
    """Compact JSON encoding — must match Kotlin's
    ``Json.encodeToString(JsonObject.serializer(), this)`` byte-for-byte.
    Kotlin's default ``kotlinx.serialization.json.Json`` uses no extra
    whitespace, separators are ``","`` and ``":"``, keys preserve insertion
    order. We use ``json.dumps(..., separators=(",", ":"), ensure_ascii=False)``
    for an exact match.
    """
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def build_aov_payload(claims: "AovClaims", issuer_did_key: str) -> dict[str, Any]:
    """Build the W3C VC 2.0 JSON-LD payload.

    Identical to Kotlin ``buildAovPayload`` (``JwsSigner.kt:39-57``):
    ``@context``, ``type`` (a two-element array), ``issuer``,
    ``validFrom``, and ``credentialSubject`` carrying the eight AoV
    claims.
    """
    return {
        "@context": [VC_CONTEXT],
        "type": [VC_TYPE, AOV_TYPE],
        "issuer": issuer_did_key,
        "validFrom": claims.valid_since,
        "credentialSubject": {
            "vc_id": claims.vc_id,
            "valid_since": claims.valid_since,
            "subject": claims.subject,
            "issuer_id": claims.issuer_id,
            "record_id": claims.record_id,
            "contract_id": claims.contract_id,
            "data_exchange_id": claims.data_exchange_id,
            "payload": claims.payload,
        },
    }


def _jws_header() -> dict[str, str]:
    return {"alg": JWS_HEADER_ALG, "typ": JWS_HEADER_TYPE}


def sign_jws(claims: "AovClaims", signing_key: SigningKey, issuer_did_key: str) -> str:
    """Sign and produce a compact JWS string.

    ``signing_key`` is a :class:`nacl.signing.SigningKey` (Ed25519).
    The signature is produced by libsodium via
    ``signing_key.sign(signing_input).signature`` — which is the
    canonical EdDSA primitive, not a hand-rolled signing function.
    """
    header_b64 = _b64url(_json_compact(_jws_header()))
    payload_b64 = _b64url(_json_compact(build_aov_payload(claims, issuer_did_key)))
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")

    # PyNaCl SigningKey.sign returns a SignedMessage; .signature is the
    # detached raw 64-byte EdDSA signature.
    signature = signing_key.sign(signing_input).signature
    signature_b64 = _b64url(signature)
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def verify_jws(jws: str, public_key: VerifyKey) -> bool:
    """Verify a compact JWS.

    Returns ``True`` if the signature is valid; ``False`` on signature
    mismatch (mirrors ``JwsSigner.kt:100-113`` semantics — bad
    signature returns false rather than throwing). Malformed JWS raises
    an exception (also matches the Kotlin test at
    ``JwsSignerTest.kt:69-77``).
    """
    parts = jws.split(".")
    if len(parts) != 3:
        raise ValueError("Compact JWS must have 3 dot-separated parts")
    signing_input = f"{parts[0]}.{parts[1]}".encode("ascii")
    signature = _b64url_decode(parts[2])
    try:
        public_key.verify(signing_input, signature)
        return True
    except BadSignatureError:
        return False


def verify_jws_with_did_key(jws: str, did_key: str) -> bool:
    """Convenience: derive the Ed25519 public key from a did:key and verify."""
    public_key = did_key_to_public_key(did_key)
    # VerifyKey accepts the raw 32-byte encoding — same bytes that did_key
    # just decoded for us.
    return verify_jws(jws, VerifyKey(bytes(public_key)))


def decode_payload(jws: str) -> dict[str, Any]:
    """Decode (without verifying) the payload middle segment of a JWS."""
    parts = jws.split(".")
    if len(parts) != 3:
        raise ValueError("Compact JWS must have 3 dot-separated parts")
    return json.loads(_b64url_decode(parts[1]))


# AoV claims model — defined at the bottom of the module so older
# pydantic-style annotations above ("AovClaims") resolve via forward
# reference. Importing this class is the canonical way callers construct
# the claims payload.
from pydantic import BaseModel  # noqa: E402


class AovClaims(BaseModel):
    """The eight AoV credentialSubject claims.

    Fields are byte-identical to ``hu.bme.mit.ftsrg.dva.api.jws.AovClaims``
    (``JwsSigner.kt:19-28``): ``vcId, validSince, subject, issuerId,
    recordId, contractId, dataExchangeId, payload``. Python field names
    are snake_case but Pydantic aliases make the JSON keys camelCase.
    """

    vc_id: str
    valid_since: str
    subject: str
    issuer_id: str
    record_id: str
    contract_id: str
    data_exchange_id: str
    payload: str

    model_config = {"populate_by_name": True}

    @property
    def vcId(self) -> str:  # noqa: N802 — parity with Kotlin property name.
        return self.vc_id