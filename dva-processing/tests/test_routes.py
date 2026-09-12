"""
End-to-end HTTP tests for the DVA Processing endpoints.

Covers:
* ``POST /evaluate`` — a passing and a failing requirement, and the 400 an
  engine we do not implement earns.
* ``POST /evaluate-batch`` — every requirement across a VLA's schema
  objects, and a VLA that declares none.
* ``POST /evaluate/from-template`` — the rendered requirement, and each of
  the upstream failures the spec documents.

The VLA Manager is stubbed at the ``requests`` call, so no upstream is
needed.
"""

from collections.abc import Iterator
from typing import Any, Optional

import pytest
import requests
from fastapi.testclient import TestClient

from dva_processing import vla_manager
from dva_processing.http import create_app

TEMPLATE_ID = "a5dee716-2129-4588-a1a2-04a4c2923a79"
MISSING_ID = "00000000-0000-0000-0000-000000000099"

PASSING_REQUIREMENT = {
    "engine": "JQ",
    "implementation": '{ success: (.actor.name | length > 0), details: "named" }',
}
FAILING_REQUIREMENT = {
    "engine": "JQ",
    "implementation": '{ success: (.verb.id | length > 0), details: "verb" }',
}

DATA = {"actor": {"name": "Jean Dupont"}}

A_TEMPLATE = {
    "id": TEMPLATE_ID,
    "name": "Field is not blank",
    "evaluationMethod": {
        "engine": "JQ",
        "implementationTemplate": (
            '{ success: (.{{ field }} | length > 0), details: "not blank" }'
        ),
    },
}


def vla(*schema_objects: dict[str, Any]) -> dict[str, Any]:
    """A minimal but valid ODCS document carrying the given schema objects."""
    return {
        "apiVersion": "v3.0.2",
        "kind": "DataContract",
        "version": "0.1.0",
        "status": "active",
        "schema": list(schema_objects),
    }


class FakeResponse:
    """The slice of ``requests.Response`` that ``fetch_template`` touches."""

    def __init__(self, status_code: int, payload: Optional[Any] = None) -> None:
        self.status_code = status_code
        self._payload = payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} error")

    def json(self) -> Any:
        if self._payload is None:
            raise ValueError("not JSON")
        return self._payload


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture
def vla_manager_returns(monkeypatch: pytest.MonkeyPatch):
    """Stub the VLA Manager with a response of the test's choosing."""

    def stub(response: FakeResponse | Exception):
        def fake_get(url: str, **kwargs: Any) -> FakeResponse:
            if isinstance(response, Exception):
                raise response
            return response

        monkeypatch.setattr(vla_manager.requests, "get", fake_get)

    return stub


# --- POST /evaluate ---------------------------------------------------


def test_evaluate_reports_a_satisfied_requirement(client: TestClient) -> None:
    response = client.post(
        "/evaluate", json={"requirement": PASSING_REQUIREMENT, "data": DATA}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["engine"] == "JQ"
    assert body["error"] is None


def test_evaluate_reports_an_unsatisfied_requirement(client: TestClient) -> None:
    response = client.post(
        "/evaluate", json={"requirement": FAILING_REQUIREMENT, "data": DATA}
    )

    assert response.status_code == 200
    assert response.json()["success"] is False


def test_evaluate_rejects_an_engine_we_do_not_implement(client: TestClient) -> None:
    """ODCS leaves `engine` a free-form string, so this is our check to make."""
    response = client.post(
        "/evaluate",
        json={
            "requirement": {"engine": "NO_SUCH_ENGINE", "implementation": "."},
            "data": DATA,
        },
    )

    assert response.status_code == 400
    assert response.json()["type"] == "UNKNOWN_ENGINE"


def test_evaluate_rejects_a_body_without_a_requirement(client: TestClient) -> None:
    response = client.post("/evaluate", json={"data": DATA})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "requirement"]


# --- POST /evaluate-batch ---------------------------------------------


def test_batch_evaluates_every_requirement_in_the_vla(client: TestClient) -> None:
    response = client.post(
        "/evaluate-batch",
        json={
            "vla": vla(
                {"name": "first", "quality": [PASSING_REQUIREMENT]},
                {
                    "name": "second",
                    "quality": [FAILING_REQUIREMENT, PASSING_REQUIREMENT],
                },
            ),
            "data": DATA,
        },
    )

    assert response.status_code == 200
    assert [r["success"] for r in response.json()] == [True, False, True]


def test_batch_of_a_vla_without_requirements_is_an_empty_array(
    client: TestClient,
) -> None:
    response = client.post(
        "/evaluate-batch",
        json={"vla": vla({"name": "no quality here"}), "data": DATA},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_batch_rejects_a_vla_that_is_not_odcs(client: TestClient) -> None:
    """`quality` belongs to a schema object; ODCS forbids it at the top level."""
    response = client.post(
        "/evaluate-batch",
        json={"vla": {"quality": [PASSING_REQUIREMENT]}, "data": DATA},
    )

    assert response.status_code == 422


# --- POST /evaluate/from-template -------------------------------------


def from_template_body(template_id: str = TEMPLATE_ID) -> dict[str, Any]:
    return {
        "templateID": template_id,
        "templateModel": {"field": "actor.name"},
        "data": DATA,
    }


def test_from_template_evaluates_the_rendered_requirement(
    client: TestClient, vla_manager_returns
) -> None:
    vla_manager_returns(FakeResponse(200, A_TEMPLATE))

    response = client.post("/evaluate/from-template", json=from_template_body())

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["engine"] == "JQ"


def test_from_template_accepts_snake_case_field_names(
    client: TestClient, vla_manager_returns
) -> None:
    vla_manager_returns(FakeResponse(200, A_TEMPLATE))

    response = client.post(
        "/evaluate/from-template",
        json={
            "template_id": TEMPLATE_ID,
            "template_model": {"field": "actor.name"},
            "data": DATA,
        },
    )

    assert response.status_code == 200


def test_from_template_reports_an_unknown_template_as_404(
    client: TestClient, vla_manager_returns
) -> None:
    vla_manager_returns(FakeResponse(404))

    response = client.post(
        "/evaluate/from-template", json=from_template_body(MISSING_ID)
    )

    assert response.status_code == 404
    assert response.json() == {
        "type": "NOT_FOUND",
        "title": "No template with the given ID exists",
    }


def test_from_template_reports_an_unreachable_vla_manager_as_502(
    client: TestClient, vla_manager_returns
) -> None:
    vla_manager_returns(requests.ConnectionError("connection refused"))

    response = client.post("/evaluate/from-template", json=from_template_body())

    assert response.status_code == 502
    assert response.json()["type"] == "BAD_GATEWAY"


def test_from_template_reports_a_template_without_a_method_as_502(
    client: TestClient, vla_manager_returns
) -> None:
    vla_manager_returns(FakeResponse(200, {"id": TEMPLATE_ID, "name": "incomplete"}))

    response = client.post("/evaluate/from-template", json=from_template_body())

    assert response.status_code == 502


def test_from_template_rejects_a_template_id_that_is_not_a_uuid(
    client: TestClient,
) -> None:
    response = client.post("/evaluate/from-template", json=from_template_body("nope"))

    assert response.status_code == 422
