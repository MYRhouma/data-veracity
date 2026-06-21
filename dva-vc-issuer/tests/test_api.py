import pytest
from fastapi.testclient import TestClient

from dva_vc_issuer.app import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "dva-vc-issuer"


class TestDidDocumentEndpoint:
    def test_did_document(self, client):
        resp = client.get("/.well-known/did.json")
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "verificationMethod" in data
        assert len(data["verificationMethod"]) == 1


class TestGenerateAoV:
    def test_generate_aov_no_api_key(self, client):
        resp = client.post("/generate_aov", json={
            "request_id": "test-001",
            "exchange_id": "xchg-001",
            "contract_id": "contract-001",
            "subject": "did:web:provider.example.com",
            "issuer_id": "dva-vc-issuer",
            "payload": {"success": True, "results": []},
        })
        assert resp.status_code == 401

    def test_generate_aov_with_api_key(self, client, monkeypatch):
        monkeypatch.setenv("DVA_API_KEY", "test-key")
        import dva_vc_issuer.config as config
        config.DVA_API_KEY = "test-key"

        resp = client.post(
            "/generate_aov",
            json={
                "request_id": "test-001",
                "exchange_id": "xchg-001",
                "contract_id": "contract-001",
                "subject": "did:web:provider.example.com",
                "issuer_id": "dva-vc-issuer",
                "payload": {"success": True, "results": []},
                "target": "self",
            },
            headers={"X-API-Key": "test-key"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "vc" in data
        assert data["vc"]["type"] == ["VerifiableCredential", "AttestationOfVeracity"]


class TestVerifyEndpoint:
    def test_verify_valid_vc(self, client, monkeypatch):
        monkeypatch.setenv("DVA_API_KEY", "test-key")
        import dva_vc_issuer.config as config
        config.DVA_API_KEY = "test-key"

        gen_resp = client.post(
            "/generate_aov",
            json={
                "request_id": "test-002",
                "exchange_id": "xchg-002",
                "contract_id": "contract-002",
                "subject": "did:web:provider.example.com",
                "issuer_id": "dva-vc-issuer",
                "payload": {"success": True, "results": []},
            },
            headers={"X-API-Key": "test-key"},
        )
        vc = gen_resp.json()["vc"]

        verify_resp = client.post(
            "/verify",
            json={"vc": vc},
            headers={"X-API-Key": "test-key"},
        )
        assert verify_resp.status_code == 200
        data = verify_resp.json()
        assert data["valid"] is True
        assert data["error"] is None

    def test_verify_tampered_vc(self, client, monkeypatch):
        monkeypatch.setenv("DVA_API_KEY", "test-key")
        import dva_vc_issuer.config as config
        config.DVA_API_KEY = "test-key"

        gen_resp = client.post(
            "/generate_aov",
            json={
                "request_id": "test-003",
                "exchange_id": "xchg-003",
                "contract_id": "contract-003",
                "subject": "did:web:provider.example.com",
                "issuer_id": "dva-vc-issuer",
                "payload": {"success": True, "results": []},
            },
            headers={"X-API-Key": "test-key"},
        )
        vc = gen_resp.json()["vc"]
        vc["credentialSubject"]["id"] = "did:web:attacker.example.com"

        verify_resp = client.post(
            "/verify",
            json={"vc": vc},
            headers={"X-API-Key": "test-key"},
        )
        assert verify_resp.status_code == 200
        data = verify_resp.json()
        assert data["valid"] is False