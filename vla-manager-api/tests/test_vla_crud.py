"""Unit tests for the VLA Manager API — VLA CRUD happy path.

Mirrors the Kotlin ``VLARoutesTest`` contract (the four operations it
covers): list, get-by-id, create, get-not-found. Adds an explicit
``DELETE /vla`` test that exercises the fail-closed 401 path when no
API key is configured.

The tests override the ``get_repo`` dependency with an in-memory
``FakeVLARepo`` so no Postgres is required.
"""

from __future__ import annotations

from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from vla_manager_api.dependencies import get_repo, get_template_repo
from vla_manager_api.main import create_app
from vla_manager_api.repo import FakeTemplateRepo, FakeVLARepo


@pytest.fixture
def fake_repo() -> FakeVLARepo:
    return FakeVLARepo()


@pytest.fixture
def fake_template_repo() -> FakeTemplateRepo:
    return FakeTemplateRepo()


@pytest.fixture
def client(
    fake_repo: FakeVLARepo,
    fake_template_repo: FakeTemplateRepo,
) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_repo] = lambda: fake_repo
    app.dependency_overrides[get_template_repo] = lambda: fake_template_repo
    return TestClient(app)


def test_list_vlas_empty_when_nothing_created(client: TestClient) -> None:
    r = client.get("/vla")
    assert r.status_code == 200
    assert r.json() == []


def test_get_vla_not_found(client: TestClient) -> None:
    r = client.get("/vla/00000000-0000-0000-0000-000000000001")
    assert r.status_code == 404


def test_create_vla_returns_id_and_appears_in_subsequent_gets(
    client: TestClient,
) -> None:
    payload = {
        "description": "Test VLA",
        "quality": [
            {"engine": "JQ", "implementation": "{ success: true }"},
        ],
    }
    r = client.post("/vla", json=payload)
    assert r.status_code == 201
    body = r.json()

    new_id = UUID(body["id"])

    # The persisted VLA carries the wrapper boilerplate + injected id.
    r2 = client.get(f"/vla/{new_id}")
    assert r2.status_code == 200
    persisted = r2.json()
    assert persisted["id"] == str(new_id)
    assert persisted["description"] == "Test VLA"
    assert persisted["apiVersion"] == "v3.0.2"
    assert persisted["kind"] == "DataContract"
    assert persisted["version"] == "0.1.0"
    assert persisted["status"] == "active"
    assert persisted["quality"] == [
        {"engine": "JQ", "implementation": "{ success: true }"}
    ]


def test_create_vla_with_minimal_body_persists(client: TestClient) -> None:
    r = client.post("/vla", json={})
    assert r.status_code == 201
    new_id = UUID(r.json()["id"])

    persisted = client.get(f"/vla/{new_id}").json()
    # Only the wrapper boilerplate + id should be present.
    assert persisted["apiVersion"] == "v3.0.2"
    assert persisted["kind"] == "DataContract"
    assert "description" not in persisted


def test_created_vla_then_listed(client: TestClient) -> None:
    # Create one
    r = client.post("/vla", json={"description": "My first VLA"})
    assert r.status_code == 201
    new_id = UUID(r.json()["id"])

    # List shows it
    listing = client.get("/vla").json()
    assert len(listing) == 1
    assert listing[0]["id"] == str(new_id)
    assert listing[0]["description"] == "My first VLA"


def test_delete_all_unauthorised_when_no_api_key(client: TestClient) -> None:
    r = client.delete("/vla")
    assert r.status_code == 401


def test_vla_id_is_a_real_uuid_v4(client: TestClient) -> None:
    r = client.post("/vla", json={"description": "x"})
    new_id = UUID(r.json()["id"])
    # Version nibble of a UUIDv4 is 4 in the 13th hex digit.
    assert str(new_id)[14] == "4"


def test_vla_from_templates_returns_404_for_missing_template(
    client: TestClient,
    fake_template_repo: FakeTemplateRepo,
) -> None:
    r = client.post(
        "/vla/from-templates",
        json={
            "qualityTemplates": [
                {"id": "00000000-0000-0000-0000-000000000099", "model": {}}
            ]
        },
    )
    assert r.status_code == 404


async def test_vla_from_templates_creates_vla_with_rendered_quality(
    client: TestClient,
    fake_template_repo: FakeTemplateRepo,
) -> None:
    import asyncio
    template_id = "3c58c2fd-6d7a-4953-9f76-7c71fc3ac7e2"
    await fake_template_repo.add(
        {
            "id": template_id,
            "name": "JQ check",
            "criterionType": "process",
            "targetAspect": "field",
            "evaluationMethod": {
                "engine": "JQ",
                "variableSchema": {"value": {"type": "string"}},
                "implementationTemplate": ".value == \"ok\"",
            },
        }
    )
    r = client.post(
        "/vla/from-templates",
        json={
            "description": "rendered VLA",
            "qualityTemplates": [
                {"id": template_id, "model": {"value": "ok"}}
            ],
        },
    )
    assert r.status_code == 201
    new_id = UUID(r.json()["id"])
    vla = client.get(f"/vla/{new_id}").json()
    assert vla["description"] == "rendered VLA"
    assert len(vla["quality"]) == 1
    assert vla["quality"][0]["engine"] == "JQ"


def test_create_vla_with_schema_field_round_trips(client: TestClient) -> None:
    # The JSON key is literally ``schema`` (not ``schema_``); pydantic
    # field alias must accept it and persist it under that key.
    payload = {
        "description": "with-schema",
        "schema": {"name": "xapi_statement", "logicalType": "object"},
    }
    r = client.post("/vla", json=payload)
    assert r.status_code == 201
    new_id = UUID(r.json()["id"])

    persisted = client.get(f"/vla/{new_id}").json()
    assert persisted["description"] == "with-schema"
    assert persisted["schema"] == {"name": "xapi_statement", "logicalType": "object"}
    # The internal pydantic field name ``schema_`` must never leak out.
    assert "schema_" not in persisted