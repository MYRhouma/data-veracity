import json
import base64
import pytest
from datetime import datetime, timezone

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

from dva_vc_issuer.signing import create_vc, verify_vc, get_did_document
from dva_vc_issuer.models import AoVRequest


@pytest.fixture
def private_key():
    return rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )


@pytest.fixture
def aov_request_data():
    return {
        "request_id": "req-001",
        "exchange_id": "xchg-001",
        "contract_id": "contract-001",
        "subject": "did:web:provider.example.com",
        "issuer_id": "dva-vc-issuer",
        "payload": {
            "success": True,
            "results": [
                {"engine": "JQ", "timestamp": "2025-06-18T12:00:00Z", "success": True}
            ],
        },
        "target": "self",
    }


class TestCreateVC:
    def test_create_vc_basic_structure(self, private_key, aov_request_data):
        vc = create_vc(aov_request_data, private_key)

        assert "@context" in vc
        assert vc["@context"] == ["https://www.w3.org/ns/credentials/v2"]
        assert vc["type"] == ["VerifiableCredential", "AttestationOfVeracity"]
        assert vc["id"] == "urn:uuid:req-001"
        assert vc["issuer"].startswith("did:web:")
        assert "validFrom" in vc
        assert "credentialSubject" in vc

    def test_create_vc_has_proof(self, private_key, aov_request_data):
        vc = create_vc(aov_request_data, private_key)

        assert "proof" in vc
        assert vc["proof"]["type"] == "JsonWebSignature2020"
        assert "jws" in vc["proof"]
        assert vc["proof"]["jws"].count(".") == 2
        assert vc["proof"]["proofPurpose"] == "assertionMethod"
        assert "verificationMethod" in vc["proof"]

    def test_create_vc_credential_subject(self, private_key, aov_request_data):
        vc = create_vc(aov_request_data, private_key)

        cs = vc["credentialSubject"]
        assert cs["id"] == "did:web:provider.example.com"
        assert cs["type"] == "DataVeracityAttestation"
        assert cs["dataExchangeId"] == "xchg-001"
        assert cs["contractId"] == "contract-001"
        assert cs["evaluationResult"]["success"] is True
        assert len(cs["evaluationResult"]["results"]) == 1

    def test_create_vc_with_failed_evaluation(self, private_key):
        data = {
            "request_id": "req-002",
            "exchange_id": "xchg-002",
            "contract_id": "contract-002",
            "subject": "did:web:provider.example.com",
            "issuer_id": "dva-vc-issuer",
            "payload": {"success": False, "results": []},
            "target": "self",
        }
        vc = create_vc(data, private_key)

        assert vc["credentialSubject"]["evaluationResult"]["success"] is False


class TestVerifyVC:
    def test_verify_valid_vc(self, private_key, aov_request_data):
        vc = create_vc(aov_request_data, private_key)
        valid, error = verify_vc(vc, private_key)

        assert valid is True
        assert error is None

    def test_verify_tampered_vc(self, private_key, aov_request_data):
        vc = create_vc(aov_request_data, private_key)
        vc["credentialSubject"]["id"] = "did:web:attacker.example.com"
        valid, error = verify_vc(vc, private_key)

        assert valid is False
        assert "tampered" in error.lower() or "mismatch" in error.lower()

    def test_verify_missing_proof(self, private_key, aov_request_data):
        vc = create_vc(aov_request_data, private_key)
        del vc["proof"]
        valid, error = verify_vc(vc, private_key)

        assert valid is False
        assert "proof" in error.lower()

    def test_verify_wrong_proof_type(self, private_key, aov_request_data):
        vc = create_vc(aov_request_data, private_key)
        vc["proof"]["type"] = "Ed25519Signature2020"
        valid, error = verify_vc(vc, private_key)

        assert valid is False
        assert "proof type" in error.lower()

    def test_verify_corrupted_signature(self, private_key, aov_request_data):
        vc = create_vc(aov_request_data, private_key)
        parts = vc["proof"]["jws"].split(".")
        parts[2] = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        vc["proof"]["jws"] = ".".join(parts)
        valid, error = verify_vc(vc, private_key)

        assert valid is False
        assert "signature" in error.lower() or "decode" in error.lower()


class TestDidDocument:
    def test_did_document_structure(self, private_key):
        doc = get_did_document(private_key)

        assert "id" in doc
        assert doc["id"].startswith("did:web:")
        assert "verificationMethod" in doc
        assert len(doc["verificationMethod"]) == 1
        assert doc["verificationMethod"][0]["type"] == "JsonWebKey2020"
        assert "publicKeyJwk" in doc["verificationMethod"][0]

    def test_did_document_public_key_jwk(self, private_key):
        doc = get_did_document(private_key)
        jwk = doc["verificationMethod"][0]["publicKeyJwk"]

        assert jwk["kty"] == "RSA"
        assert jwk["alg"] == "PS256"
        assert "n" in jwk
        assert "e" in jwk
        assert jwk["use"] == "sig"


class TestKeyManagement:
    def test_key_pair_generation(self, tmp_path, monkeypatch):
        import importlib
        monkeypatch.setenv("DVA_VC_KEY_PATH", str(tmp_path / "test_key.pem"))
        import dva_vc_issuer.config as config_mod
        importlib.reload(config_mod)
        import dva_vc_issuer.keys as keys_mod
        importlib.reload(keys_mod)

        key1 = keys_mod.load_or_create_key_pair()
        assert key1 is not None

        key2 = keys_mod.load_or_create_key_pair()
        assert key2 is not None

        pub1 = key1.public_key().public_numbers()
        pub2 = key2.public_key().public_numbers()
        assert pub1.n == pub2.n, "Should load same key from disk on second call"

    def test_key_persistence_to_disk(self, tmp_path, monkeypatch):
        import importlib
        key_path = tmp_path / "keys" / "private_key.pem"
        monkeypatch.setenv("DVA_VC_KEY_PATH", str(key_path))
        import dva_vc_issuer.config as config_mod
        importlib.reload(config_mod)
        import dva_vc_issuer.keys as keys_mod
        importlib.reload(keys_mod)

        assert not key_path.exists()
        keys_mod.load_or_create_key_pair()
        assert key_path.exists(), "Key file should be created on disk"

        pub_path = key_path.with_suffix(".pub.pem")
        assert pub_path.exists(), "Public key file should also be created"