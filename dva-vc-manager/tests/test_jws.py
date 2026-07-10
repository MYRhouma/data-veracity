"""JWS sign+verify tests — mirror ``JwsSignerTest.kt`` behaviour exactly."""

from __future__ import annotations

import pytest
from nacl.signing import SigningKey, VerifyKey

from dva_vc_manager.signing import AovClaims, sign_jws, verify_jws


def _sample_claims() -> AovClaims:
    return AovClaims(
        vc_id="urn:uuid:11111111-2222-3333-4444-555555555555",
        valid_since="2024-01-01T00:00:00Z",
        subject="did:web:data-consumer.example",
        issuer_id="did:web:data-provider.example",
        record_id="rec-0001",
        contract_id="contract-0001",
        data_exchange_id="xchg-0001",
        payload="checksum:sha256:abcdef0123456789",
    )


_KNOWN_DID_KEY = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"


def test_signs_and_verifies_a_valid_aov() -> None:
    signing_key = SigningKey.generate()
    public_key = VerifyKey(bytes(signing_key.verify_key))

    jws = sign_jws(_sample_claims(), signing_key, _KNOWN_DID_KEY)

    assert jws, "JWS must not be empty"
    assert jws.count(".") == 2, "Compact JWS must have 3 dot-separated parts"

    ok = verify_jws(jws, public_key)
    assert ok, "verify_jws must return True for a valid signature"


def test_tampered_payload_fails_verification() -> None:
    signing_key = SigningKey.generate()
    public_key = VerifyKey(bytes(signing_key.verify_key))

    jws = sign_jws(_sample_claims(), signing_key, _KNOWN_DID_KEY)
    parts = jws.split(".")
    # Flip the first character of the payload segment.
    first_char = parts[1][0]
    flipped_char = "B" if first_char == "A" else "A"
    parts[1] = flipped_char + parts[1][1:]
    tampered_jws = f"{parts[0]}.{parts[1]}.{parts[2]}"

    ok = verify_jws(tampered_jws, public_key)
    assert ok is False, "verify_jws must return False for a tampered payload"


def test_rejection_of_a_clearly_malformed_jws() -> None:
    signing_key = SigningKey.generate()
    public_key = VerifyKey(bytes(signing_key.verify_key))

    with pytest.raises(Exception):
        verify_jws("not.a.jws.at.all", public_key)


def test_payload_shape_includes_context_type_issuer_validfrom_subject() -> None:
    """Validate the W3C VC JSON-LD structure — byte-identical to the
    Kotlin ``buildAovPayload`` at ``JwsSigner.kt:39-57``."""
    from dva_vc_manager.signing import build_aov_payload, decode_payload

    signing_key = SigningKey.generate()
    jws = sign_jws(_sample_claims(), signing_key, _KNOWN_DID_KEY)
    payload = decode_payload(jws)
    assert payload["@context"] == ["https://www.w3.org/2018/credentials/v1"]
    assert payload["type"] == ["VerifiableCredential", "AttestationOfVeracity"]
    assert payload["issuer"] == _KNOWN_DID_KEY
    assert payload["validFrom"] == "2024-01-01T00:00:00Z"
    sub = payload["credentialSubject"]
    assert sub["vc_id"] == "urn:uuid:11111111-2222-3333-4444-555555555555"
    assert sub["valid_since"] == "2024-01-01T00:00:00Z"
    assert sub["subject"] == "did:web:data-consumer.example"
    assert sub["issuer_id"] == "did:web:data-provider.example"
    assert sub["record_id"] == "rec-0001"
    assert sub["contract_id"] == "contract-0001"
    assert sub["data_exchange_id"] == "xchg-0001"
    assert sub["payload"] == "checksum:sha256:abcdef0123456789"