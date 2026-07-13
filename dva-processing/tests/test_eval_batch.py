"""Tests for the new ``POST /evaluate-batch`` endpoint.

Validates the step-4 → step-5 transition of the synchronous 8-step
attestation flow. The DVA API posts the full VLA + data here; the
processing service iterates over ``vla.schema[*].quality[*]`` and
returns one :class:`EvaluationResult` per requirement.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from dva_processing.http import app


client = TestClient(app)


def test_evaluate_batch_returns_one_result_per_requirement() -> None:
    vla = {
        "schema": [
            {
                "name": "xapi_statement",
                "quality": [
                    {
                        "engine": "JQ",
                        "implementation": '{ success: .result.success, details: "result.success" }',
                    },
                    {
                        "engine": "JQ",
                        "implementation": '{ success: (.actor.name | contains("Dupont")), details: "actor contains Dupont" }',
                    },
                ],
            },
        ],
    }
    data = {
        "actor": {"name": "Jean Dupont"},
        "result": {"success": True},
    }

    r = client.post("/evaluate-batch", json={"vla": vla, "data": data})
    assert r.status_code == 200, r.text
    results = r.json()
    assert len(results) == 2
    assert all(res["success"] for res in results)
    assert results[0]["engine"] == "JQ"
    assert results[1]["engine"] == "JQ"


def test_evaluate_batch_preserves_order() -> None:
    """The order of returned results matches the order of requirements in
    the VLA — the DVA API zips them later against the requirement
    listings, so order is significant."""
    vla = {
        "schema": [
            {
                "quality": [
                    {
                        "engine": "JQ",
                        "implementation": '{ success: true, details: "ok" }',
                    },
                ],
            },
            {
                "quality": [
                    {
                        "engine": "JQ",
                        "implementation": '{ success: false, details: "fail" }',
                    },
                ],
            },
        ],
    }
    r = client.post("/evaluate-batch", json={"vla": vla, "data": {}})
    assert r.status_code == 200
    results = r.json()
    assert len(results) == 2
    assert results[0]["success"] is True
    assert results[1]["success"] is False


def test_evaluate_batch_empty_vla_returns_empty_list() -> None:
    r = client.post("/evaluate-batch", json={"vla": {}, "data": {}})
    assert r.status_code == 200
    assert r.json() == []


def test_evaluate_batch_vla_with_no_schema_returns_empty_list() -> None:
    r = client.post(
        "/evaluate-batch",
        json={"vla": {"description": "no schema"}, "data": {}},
    )
    assert r.status_code == 200
    assert r.json() == []


def test_evaluate_batch_vla_with_schema_but_no_quality_returns_empty_list() -> None:
    r = client.post(
        "/evaluate-batch",
        json={"vla": {"schema": [{"name": "no_quality"}]}, "data": {}},
    )
    assert r.status_code == 200
    assert r.json() == []


def test_evaluate_batch_tolerates_invalid_requirement() -> None:
    """A malformed requirement should still produce an EvaluationResult
    with success=False and an error message — not 500 the whole batch.
    Mirrors the per-requirement try/except in ``handle_aov_request``
    (``processing.py:49-68``)."""
    vla = {
        "schema": [
            {
                "quality": [
                    {"engine": "JQ", "implementation": '{ success: true, details: "ok" }'},
                    {"engine": "MADE_UP_ENGINE", "implementation": "x"},
                ],
            },
        ],
    }
    r = client.post("/evaluate-batch", json={"vla": vla, "data": {}})
    assert r.status_code == 200
    results = r.json()
    assert len(results) == 2
    assert results[0]["success"] is True
    assert results[1]["success"] is False
    assert results[1]["error"] is not None


def test_evaluate_batch_handles_malformed_schema_gracefully() -> None:
    """If schema isn't a list or quality isn't a list, the batch should
    still complete with what *is* parseable."""
    r = client.post(
        "/evaluate-batch",
        json={
            "vla": {
                "schema": "not a list but the route must not crash",
            },
            "data": {},
        },
    )
    assert r.status_code == 200
    assert r.json() == []


def test_evaluate_batch_accepts_schema_as_dict() -> None:
    """VLA Manager API stores ``schema`` as a single dict (not a list).
    The processor must still iterate the dict's ``quality`` array and
    evaluate each requirement."""
    vla = {
        "description": "schema-as-dict VLA (VLA Manager's natural shape)",
        "schema": {
            "name": "xapi_statement",
            "logicalType": "object",
            "quality": [
                {"engine": "JQ", "implementation": '{ success: true, details: "ok" }'},
                {"engine": "JQ", "implementation": '{ success: true, details: "ok 2" }'},
            ],
        },
    }
    r = client.post("/evaluate-batch", json={"vla": vla, "data": {}})
    assert r.status_code == 200
    results = r.json()
    assert len(results) == 2
    assert all(res["success"] for res in results)


def test_evaluate_batch_accepts_top_level_quality_when_no_schema() -> None:
    """Some VLAs have no ``schema`` field — quality lives at the top
    level instead. The processor must still evaluate them."""
    vla_flat = {
        "description": "VLA with top-level quality only (no schema key)",
        "quality": [
            {"engine": "JQ", "implementation": '{ success: true, details: "ok" }'},
            {"engine": "JQ", "implementation": '{ success: false, details: "fail" }'},
        ],
    }
    r = client.post("/evaluate-batch", json={"vla": vla_flat, "data": {}})
    assert r.status_code == 200
    results = r.json()
    assert len(results) == 2
    assert results[0]["success"] is True
    assert results[1]["success"] is False


def test_evaluate_batch_handles_top_level_quality_as_dict() -> None:
    """A paranoid edge case — ``quality`` is a single dict, not a list.
    The processor should still iterate it as a single requirement."""
    r = client.post(
        "/evaluate-batch",
        json={
            "vla": {
                "quality": {"engine": "JQ", "implementation": '{ success: true, details: "ok" }'},
            },
            "data": {},
        },
    )
    assert r.status_code == 200
    results = r.json()
    assert len(results) == 1
    assert results[0]["success"] is True


def test_evaluate_batch_handles_vla_with_no_quality_at_all() -> None:
    """A VLA with no schema and no quality at all — empty result, 200."""
    r = client.post(
        "/evaluate-batch",
        json={"vla": {"description": "nothing to check"}, "data": {}},
    )
    assert r.status_code == 200
    assert r.json() == []