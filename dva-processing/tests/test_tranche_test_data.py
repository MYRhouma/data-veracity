"""
Validates that the tranche test data files produce the expected tranche levels.
"""

import json
from pathlib import Path

import pytest
from dva_processing.tranches import evaluate_tranches


TEST_DATA_DIR = Path(__file__).parent.parent.parent / "test-env" / "test-data" / "aov"


def load_tranche_test_data(tranche_name: str) -> dict:
    path = TEST_DATA_DIR / tranche_name / "request.json"
    with open(path) as f:
        return json.load(f)


class TestTrancheTestData:
    def test_incomplete_data_has_no_actor(self):
        data = load_tranche_test_data("tranche_incomplete")
        result = evaluate_tranches(data["data"])
        assert result["tranche_level"] == "incomplete"
        assert result["percentage"] == 0
        assert "actor" in result["mandatory_failed"]

    def test_basic_data_has_all_mandatory_no_optional(self):
        data = load_tranche_test_data("tranche_basic")
        result = evaluate_tranches(data["data"])
        assert result["tranche_level"] == "basic"
        assert result["percentage"] == 40
        assert len(result["mandatory_passed"]) == 6
        assert len(result["mandatory_failed"]) == 0
        assert len(result["optional_passed"]) == 0

    def test_enriched_data_has_mandatory_plus_two_optional(self):
        data = load_tranche_test_data("tranche_enriched")
        result = evaluate_tranches(data["data"])
        assert result["tranche_level"] == "enriched"
        assert result["percentage"] == 70
        assert len(result["mandatory_passed"]) == 6
        assert len(result["optional_passed"]) >= 2

    def test_full_data_has_all_nine_fields(self):
        data = load_tranche_test_data("tranche_full")
        result = evaluate_tranches(data["data"])
        assert result["tranche_level"] == "full"
        assert result["percentage"] == 100
        assert result["total_passed"] == 9
        assert result["total_failed"] == 0

    def test_tranche_progression(self):
        levels = []
        percentages = []
        for tranche in ["tranche_incomplete", "tranche_basic", "tranche_enriched", "tranche_full"]:
            data = load_tranche_test_data(tranche)
            result = evaluate_tranches(data["data"])
            levels.append(result["tranche_level"])
            percentages.append(result["percentage"])

        assert levels == ["incomplete", "basic", "enriched", "full"]
        assert percentages == [0, 40, 70, 100]