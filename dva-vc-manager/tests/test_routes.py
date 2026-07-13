"""End-to-end HTTP tests for the DVA VC Manager — mirrors Kotlin
``AoVSyncRoutesTest.kt`` + the admin routes test.

Covers:
* ``POST /aov/issue`` happy path — 200, JWS round-trips through
  ``POST /aov/verify``.
* ``POST /aov/verify`` rejects a tampered JWS.
* ``POST /aov/verify`` fails-closed when whitelist is empty.
* ``POST /aov/verify`` rejects when attester not whitelisted.
* ``POST /aov/verify`` rejects a clearly malformed JWS with 400.
* Admin endpoints fail-closed 401 when no API key is configured.
"""

from __future__ import annotations

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from nacl.signing import SigningKey

from dva_vc_manager.dependencies import get_whitelist
from dva_vc_manager.main import create_app
from dva_vc_manager.whitelist import FakeWhitelist

_KNOWN_DID_KEY = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"


@pytest.fixture
def whitelist() -> FakeWhitelist:
    return FakeWhitelist()


@pytest.fixture
def client(whitelist: FakeWhitelist, monkeypatch: pytest.MonkeyPatch, tmp_path) -> TestClient:
    # Sign to a temp key file so tests don't touch the real /data path.
    monkeypatch.setenv("DVA_VC_MANAGER_SIGNING_KEY_PATH", str(tmp_path / "key.pem"))
    # Re-read config because the module already imported it.
    from dva_vc_manager import config as cfg_module
    cfg_module.cfg.signing_key_path = str(tmp_path / "key.pem")
    cfg_module.cfg.api_key = ""  # admin disabled (fail-closed)
    cfg_module.cfg.postgres_dsn = ""  # Forces FakeWhitelist via dependency override

    app = create_app()
    app.dependency_overrides[get_whitelist] = lambda: whitelist
    return TestClient(app)


def _issue_request():
    return {
        "vc_id": str(uuid4()),
        "valid_since": "2024-01-01T00:00:00Z",
        "subject": "did:web:data-consumer.example",
        "issuer_id": "did:web:data-provider.example",
        "record_id": "rec-0001",
        "contract_id": "contract-0001",
        "data_exchange_id": "xchg-0001",
        "payload": "checksum:sha256:abcdef0123456789",
        "evaluation_results": [
            {
                "engine": "JQ",
                "timestamp": "2024-01-01T00:00:00Z",
                "success": True,
                "details": "ok",
                "error": None,
            }
        ],
    }


def test_aov_issue_returns_jws_and_did_key(client: TestClient) -> None:
    r = client.post("/aov/issue", json=_issue_request())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["jws"]
    assert body["jws"].count(".") == 2
    assert body["issuerDidKey"].startswith("did:key:z6Mk")
    assert body["vcIssuedDate"]


async def test_aov_issue_then_verify_round_trip(client: TestClient, whitelist: FakeWhitelist) -> None:
    payload = _issue_request()
    # Issue
    r = client.post("/aov/issue", json=payload)
    assert r.status_code == 200
    body = r.json()
    jws = body["jws"]
    issuer_did_key = body["issuerDidKey"]

    # Whitelist the issuer (await because FakeWhitelist.add is async)
    await whitelist.add(issuer_did_key, label="self")

    # Verify
    r2 = client.post(
        "/aov/verify",
        json={"jws": jws, "attesterDidKey": issuer_did_key},
    )
    assert r2.status_code == 200, r2.text
    body2 = r2.json()
    assert body2["verified"] is True
    assert body2["payload"] is not None
    assert body2["payload"]["credentialSubject"]["vc_id"] == payload["vc_id"]


async def test_aov_verify_rejects_tampered_jws(client: TestClient, whitelist: FakeWhitelist) -> None:
    r = client.post("/aov/issue", json=_issue_request())
    jws = r.json()["jws"]
    issuer_did_key = r.json()["issuerDidKey"]
    await whitelist.add(issuer_did_key)

    parts = jws.split(".")
    # Flip first char of payload
    first_char = parts[1][0]
    flipped = "B" if first_char == "A" else "A"
    parts[1] = flipped + parts[1][1:]
    tampered = f"{parts[0]}.{parts[1]}.{parts[2]}"

    r2 = client.post(
        "/aov/verify",
        json={"jws": tampered, "attesterDidKey": issuer_did_key},
    )
    assert r2.status_code == 200
    assert r2.json()["verified"] is False
    assert r2.json()["reason"] == "signature mismatch"


def test_aov_verify_fails_closed_when_whitelist_empty(
    client: TestClient, whitelist: FakeWhitelist
) -> None:
    # Whitelist is empty by default.
    r = client.post(
        "/aov/verify",
        json={"jws": "x.y.z", "attester_did_key": _KNOWN_DID_KEY},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["verified"] is False
    assert body["reason"] == "whitelist is not configured; verification is disabled"


async def test_aov_verify_rejects_when_attester_not_whitelisted(
    client: TestClient, whitelist: FakeWhitelist
) -> None:
    # Pre-populate with some other key so the whitelist is non-empty.
    await whitelist.add("did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK")
    # Verify with a different attester DID.
    r = client.post(
        "/aov/verify",
        json={
            "jws": "a.b.c",
            "attester_did_key": "did:key:z6MkmchsyWzT9T7K4KKMZHvB8fnZrJ4MSqt7pFztvJ237oVq",
        },
    )
    assert r.status_code == 200
    assert r.json()["reason"] == "attester not whitelisted"


async def test_aov_verify_rejects_malformed_jws_with_400(
    client: TestClient, whitelist: FakeWhitelist
) -> None:
    await whitelist.add(_KNOWN_DID_KEY)
    r = client.post(
        "/aov/verify",
        json={"jws": "not.a.jws.at.all", "attester_did_key": _KNOWN_DID_KEY},
    )
    assert r.status_code == 400


def test_admin_whitelist_unauthorised_when_no_api_key(client: TestClient) -> None:
    # Default config: api_key == "" → admin disabled.
    r = client.get("/admin/whitelist")
    assert r.status_code == 401
    r = client.post("/admin/whitelist", json={"did_key": _KNOWN_DID_KEY})
    assert r.status_code == 401
    r = client.delete(f"/admin/whitelist/{_KNOWN_DID_KEY}")
    assert r.status_code == 401
    r = client.get("/admin/keys")
    assert r.status_code == 401