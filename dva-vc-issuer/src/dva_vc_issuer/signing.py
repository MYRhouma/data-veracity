import base64
import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.padding import PSS, MGF1
from jose import jws as jose_jws

from .config import DVA_VC_DID_DOMAIN, DVA_VC_ISSUER_ID, DVA_VC_KEY_ID
from .keys import get_public_key_jwk


def _did_web() -> str:
    return f"did:web:{DVA_VC_DID_DOMAIN}"


def _verification_method() -> str:
    return f"{_did_web()}#{DVA_VC_KEY_ID}"


def _canonical_json(data: dict[str, Any]) -> bytes:
    return json.dumps(
        data, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _hash_base64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def create_vc(
    request_data: dict[str, Any],
    private_key: rsa.RSAPrivateKey,
) -> dict[str, Any]:
    vc_id = f"urn:uuid:{request_data.get('request_id', '')}"
    issuer_did = _did_web()
    now_iso = datetime.now(timezone.utc).isoformat()

    payload = request_data.get("payload", {})
    success = payload.get("success", False)
    results = payload.get("results", [])

    credential_subject: dict[str, Any] = {
        "id": request_data.get("subject", ""),
        "type": "DataVeracityAttestation",
        "dataExchangeId": request_data.get("exchange_id", ""),
        "contractId": request_data.get("contract_id", ""),
        "attesterId": request_data.get("issuer_id", ""),
        "evaluationResult": {
            "success": success,
            "results": results,
        },
    }

    tranche_data = payload.get("tranche_evaluation")
    if tranche_data:
        credential_subject["trancheEvaluation"] = tranche_data

    vc: dict[str, Any] = {
        "@context": [
            "https://www.w3.org/ns/credentials/v2",
        ],
        "id": vc_id,
        "type": ["VerifiableCredential", "AttestationOfVeracity"],
        "issuer": issuer_did,
        "validFrom": now_iso,
        "credentialSubject": credential_subject,
    }

    proof = _sign_vc(vc, private_key)
    vc["proof"] = proof

    return vc


def _sign_vc(vc: dict[str, Any], private_key: rsa.RSAPrivateKey) -> dict[str, Any]:
    header = {
        "alg": "PS256",
        "typ": "JWT",
        "kid": _verification_method(),
    }

    vc_without_proof = {k: v for k, v in vc.items() if k != "proof"}
    payload_json = _canonical_json(vc_without_proof)

    header_b64 = _hash_base64url(json.dumps(header, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _hash_base64url(payload_json)

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

    signature = private_key.sign(
        signing_input,
        PSS(mgf=MGF1(hashes.SHA256()), salt_length=32),
        hashes.SHA256(),
    )
    signature_b64 = _hash_base64url(signature)

    jws_value = f"{header_b64}.{payload_b64}.{signature_b64}"

    return {
        "type": "JsonWebSignature2020",
        "created": datetime.now(timezone.utc).isoformat(),
        "proofPurpose": "assertionMethod",
        "verificationMethod": _verification_method(),
        "jws": jws_value,
    }


def verify_vc(vc: dict[str, Any], private_key: rsa.RSAPrivateKey) -> tuple[bool, str | None]:
    proof = vc.get("proof")
    if not proof or proof.get("type") != "JsonWebSignature2020":
        return False, "Missing or invalid proof type"

    jws_value = proof.get("jws")
    if not jws_value or jws_value.count(".") != 2:
        return False, "Invalid JWS format"

    parts = jws_value.split(".")
    header_b64, payload_b64, signature_b64 = parts

    try:
        signature = base64.urlsafe_b64decode(signature_b64 + "==")
    except Exception:
        return False, "Failed to decode signature"

    vc_without_proof = {k: v for k, v in vc.items() if k != "proof"}
    expected_payload = _canonical_json(vc_without_proof)
    expected_payload_b64 = _hash_base64url(expected_payload)

    if payload_b64 != expected_payload_b64:
        return False, "Payload tampered — hash mismatch"

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

    try:
        private_key.public_key().verify(
            signature,
            signing_input,
            PSS(mgf=MGF1(hashes.SHA256()), salt_length=32),
            hashes.SHA256(),
        )
    except Exception as e:
        return False, f"Signature verification failed: {e}"

    return True, None


def get_did_document(private_key: rsa.RSAPrivateKey) -> dict[str, Any]:
    public_jwk = get_public_key_jwk(private_key)
    return {
        "@context": [
            "https://www.w3.org/ns/did/v1",
            "https://w3id.org/security/suites/jws-2020/v1",
        ],
        "id": _did_web(),
        "verificationMethod": [
            {
                "id": _verification_method(),
                "type": "JsonWebKey2020",
                "controller": _did_web(),
                "publicKeyJwk": public_jwk,
            }
        ],
        "assertionMethod": [_verification_method()],
    }