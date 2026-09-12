"""
The spec shares schemas with the other DVA components through
``docs/spec/components.yaml`` and refers to them with a relative ``$ref``.  The
docs page resolves that against the URL it loaded the spec from, so the shared
document has to be served next to ``openapi_url`` - otherwise the references
dangle and Swagger UI renders nothing for them.
"""

from pathlib import Path
from typing import Any

import pytest
import yaml
from fastapi.testclient import TestClient

from dva_processing.config import cfg
from dva_processing.http import create_app

SPEC = Path(__file__).resolve().parents[2] / "docs" / "spec" / "dva-processing.yaml"
SHARED = SPEC.parent / "components.yaml"


def _refs(node: Any) -> list[str]:
    """Every ``$ref`` string anywhere in ``node``."""
    if isinstance(node, dict):
        found = [node["$ref"]] if isinstance(node.get("$ref"), str) else []
        return found + [r for v in node.values() for r in _refs(v)]
    if isinstance(node, list):
        return [r for v in node for r in _refs(v)]
    return []


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(cfg, "openapi_file", str(SPEC))
    return TestClient(create_app())


def test_the_spec_refers_to_the_shared_document() -> None:
    """Guards the tests below: they would pass trivially if nothing were shared."""
    external = [
        r for r in _refs(yaml.safe_load(SPEC.read_text())) if "components.yaml" in r
    ]
    assert external, "expected the spec to share schemas via components.yaml"
    assert all(r.startswith("./components.yaml#/schemas/") for r in external), external


def test_shared_document_is_served_next_to_the_spec(client: TestClient) -> None:
    """``./components.yaml`` relative to /swagger/openapi.json is this path."""
    response = client.get("/swagger/components.yaml")

    assert response.status_code == 200
    assert yaml.safe_load(response.text) == yaml.safe_load(SHARED.read_text())


def test_every_shared_ref_resolves_against_what_is_served(client: TestClient) -> None:
    served = client.get("/swagger/openapi.json").json()
    shared = yaml.safe_load(client.get("/swagger/components.yaml").text)

    for ref in set(_refs(served)):
        document, _, pointer = ref.partition("#")
        target = shared if document == "./components.yaml" else served
        assert not document or document == "./components.yaml", (
            f"unknown document in {ref}"
        )
        node: Any = target
        for token in pointer.removeprefix("/").split("/"):
            assert token in node, f"{ref} does not resolve ({token!r} missing)"
            node = node[token]


def test_the_served_spec_documents_every_route(client: TestClient) -> None:
    """The hand-written spec is served instead of the generated one, so
    nothing keeps the two in step but a check like this."""
    served = client.get("/swagger/openapi.json").json()
    routed = {
        route.path
        for route in create_app().routes
        if getattr(route, "include_in_schema", False)
    }

    assert routed <= served["paths"].keys()


def test_missing_shared_document_is_a_clean_404(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Mounting the spec without components.yaml must not yield a 500."""
    spec = tmp_path / "openapi.yaml"
    spec.write_text(SPEC.read_text(), encoding="utf-8")
    monkeypatch.setattr(cfg, "openapi_file", str(spec))

    assert TestClient(create_app()).get("/swagger/components.yaml").status_code == 404
