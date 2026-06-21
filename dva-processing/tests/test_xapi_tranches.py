"""
Tests for xAPI field check JQ templates and tranche evaluation.
"""

import pytest
from dva_processing.xapi_checks import (
    XAPI_FIELD_CHECKS,
    MANDATORY_FIELD_NAMES,
    OPTIONAL_FIELD_NAMES,
    MANDATORY_COUNT,
    OPTIONAL_COUNT,
    TrancheLevel,
    evaluate_tranche_level,
    TRANCHE_PERCENTAGES,
)
from dva_processing.engines.jq import eval_expression
from dva_processing.tranches import evaluate_tranches


FULL_XAPI = {
    "statement": {
        "actor": {
            "objectType": "Agent",
            "name": "Benjamin",
            "mbox": "mailto:Benjamin@inokufu.com",
        },
        "verb": {
            "id": "http://id.tincanapi.com/verb/reviewed",
            "display": {"en-US": "reviewed"},
        },
        "object": {
            "id": "https://www.youtube.com/watch?v=AZpJe-GwAIw",
            "objectType": "Activity",
            "definition": {
                "type": "https://w3id.org/xapi/acrossx/activities/webpage",
                "name": {"en": "Test"},
                "extensions": {
                    "https://w3id.org/xapi/acrossx/extensions/type": "website"
                },
            },
        },
        "timestamp": "2024-09-26T14:06:13.369Z",
        "context": {
            "language": "en",
            "extensions": {
                "http://schema.org/extension/username": "Benjamin",
            },
        },
        "result": {
            "score": {"raw": 5, "min": 0, "max": 10},
            "response": "the best",
        },
    }
}


MINIMAL_XAPI = {
    "statement": {
        "actor": {
            "objectType": "Agent",
            "mbox": "mailto:user@example.com",
        },
        "verb": {
            "id": "http://id.tincanapi.com/verb/accessed",
        },
        "object": {
            "id": "https://example.com/activity",
            "objectType": "Activity",
            "definition": {
                "type": "http://adlnet.gov/expapi/activities/activity",
            },
        },
        "timestamp": "2024-09-26T14:06:13.369Z",
        "context": {
            "language": "en",
        },
    }
}


NO_ACTOR = {"statement": {"verb": {"id": "http://example.com/verb"}, "object": {"id": "https://example.com/obj"}, "timestamp": "2024-01-01T00:00:00Z", "context": {"language": "en"}}}


class TestXapiFieldCheckDefinitions:
    def test_total_check_count_is_9(self):
        assert len(XAPI_FIELD_CHECKS) == 9

    def test_mandatory_count_is_6(self):
        assert MANDATORY_COUNT == 6

    def test_optional_count_is_3(self):
        assert OPTIONAL_COUNT == 3

    def test_all_checks_have_jq_expressions(self):
        for check in XAPI_FIELD_CHECKS:
            assert check.jq_expression, f"Check {check.name} has no JQ expression"
            assert len(check.jq_expression) > 20

    def test_mandatory_field_names(self):
        assert "actor" in MANDATORY_FIELD_NAMES
        assert "verb" in MANDATORY_FIELD_NAMES
        assert "object_id" in MANDATORY_FIELD_NAMES
        assert "object_definition" in MANDATORY_FIELD_NAMES
        assert "timestamp" in MANDATORY_FIELD_NAMES
        assert "context" in MANDATORY_FIELD_NAMES

    def test_optional_field_names(self):
        assert "result" in OPTIONAL_FIELD_NAMES
        assert "context_extensions" in OPTIONAL_FIELD_NAMES
        assert "object_extensions" in OPTIONAL_FIELD_NAMES


class TestJqExpressionsAgainstFullXapi:
    @pytest.fixture
    def full_data(self):
        return FULL_XAPI

    def test_actor_check_passes(self, full_data):
        results = eval_expression(full_data, next(c.jq_expression for c in XAPI_FIELD_CHECKS if c.name == "actor"))
        assert all(r.success for r in results)

    def test_verb_check_passes(self, full_data):
        results = eval_expression(full_data, next(c.jq_expression for c in XAPI_FIELD_CHECKS if c.name == "verb"))
        assert all(r.success for r in results)

    def test_object_id_check_passes(self, full_data):
        results = eval_expression(full_data, next(c.jq_expression for c in XAPI_FIELD_CHECKS if c.name == "object_id"))
        assert all(r.success for r in results)

    def test_object_definition_check_passes(self, full_data):
        results = eval_expression(full_data, next(c.jq_expression for c in XAPI_FIELD_CHECKS if c.name == "object_definition"))
        assert all(r.success for r in results)

    def test_timestamp_check_passes(self, full_data):
        results = eval_expression(full_data, next(c.jq_expression for c in XAPI_FIELD_CHECKS if c.name == "timestamp"))
        assert all(r.success for r in results)

    def test_context_check_passes(self, full_data):
        results = eval_expression(full_data, next(c.jq_expression for c in XAPI_FIELD_CHECKS if c.name == "context"))
        assert all(r.success for r in results)

    def test_result_check_passes(self, full_data):
        results = eval_expression(full_data, next(c.jq_expression for c in XAPI_FIELD_CHECKS if c.name == "result"))
        assert all(r.success for r in results)

    def test_context_extensions_check_passes(self, full_data):
        results = eval_expression(full_data, next(c.jq_expression for c in XAPI_FIELD_CHECKS if c.name == "context_extensions"))
        assert all(r.success for r in results)

    def test_object_extensions_check_passes(self, full_data):
        results = eval_expression(full_data, next(c.jq_expression for c in XAPI_FIELD_CHECKS if c.name == "object_extensions"))
        assert all(r.success for r in results)


class TestJqExpressionsAgainstMinimalXapi:
    @pytest.fixture
    def minimal_data(self):
        return MINIMAL_XAPI

    def test_actor_check_passes(self, minimal_data):
        results = eval_expression(minimal_data, next(c.jq_expression for c in XAPI_FIELD_CHECKS if c.name == "actor"))
        assert all(r.success for r in results)

    def test_verb_check_passes(self, minimal_data):
        results = eval_expression(minimal_data, next(c.jq_expression for c in XAPI_FIELD_CHECKS if c.name == "verb"))
        assert all(r.success for r in results)

    def test_object_id_check_passes(self, minimal_data):
        results = eval_expression(minimal_data, next(c.jq_expression for c in XAPI_FIELD_CHECKS if c.name == "object_id"))
        assert all(r.success for r in results)

    def test_object_definition_check_passes(self, minimal_data):
        results = eval_expression(minimal_data, next(c.jq_expression for c in XAPI_FIELD_CHECKS if c.name == "object_definition"))
        assert all(r.success for r in results)

    def test_timestamp_check_passes(self, minimal_data):
        results = eval_expression(minimal_data, next(c.jq_expression for c in XAPI_FIELD_CHECKS if c.name == "timestamp"))
        assert all(r.success for r in results)

    def test_context_check_passes(self, minimal_data):
        results = eval_expression(minimal_data, next(c.jq_expression for c in XAPI_FIELD_CHECKS if c.name == "context"))
        assert all(r.success for r in results)

    def test_result_check_fails(self, minimal_data):
        results = eval_expression(minimal_data, next(c.jq_expression for c in XAPI_FIELD_CHECKS if c.name == "result"))
        assert not all(r.success for r in results)

    def test_context_extensions_check_fails(self, minimal_data):
        results = eval_expression(minimal_data, next(c.jq_expression for c in XAPI_FIELD_CHECKS if c.name == "context_extensions"))
        assert not all(r.success for r in results)

    def test_object_extensions_check_fails(self, minimal_data):
        results = eval_expression(minimal_data, next(c.jq_expression for c in XAPI_FIELD_CHECKS if c.name == "object_extensions"))
        assert not all(r.success for r in results)


class TestJqExpressionFailures:
    def test_actor_missing_fails(self):
        results = eval_expression(NO_ACTOR, next(c.jq_expression for c in XAPI_FIELD_CHECKS if c.name == "actor"))
        assert not all(r.success for r in results)

    def test_empty_data_fails_all(self):
        empty = {"statement": {}}
        for check in XAPI_FIELD_CHECKS:
            results = eval_expression(empty, check.jq_expression)
            assert not all(r.success for r in results), f"Check {check.name} should fail on empty statement"


class TestTrancheLevelEvaluation:
    def test_incomplete_when_no_mandatory(self):
        assert evaluate_tranche_level([]) == TrancheLevel.INCOMPLETE

    def test_incomplete_when_some_mandatory_missing(self):
        assert evaluate_tranche_level(["actor", "verb"]) == TrancheLevel.INCOMPLETE

    def test_basic_when_all_mandatory_no_optional(self):
        assert evaluate_tranche_level(MANDATORY_FIELD_NAMES) == TrancheLevel.BASIC

    def test_basic_when_one_optional(self):
        fields = MANDATORY_FIELD_NAMES + ["result"]
        assert evaluate_tranche_level(fields) == TrancheLevel.BASIC

    def test_enriched_when_two_optional(self):
        fields = MANDATORY_FIELD_NAMES + ["result", "context_extensions"]
        assert evaluate_tranche_level(fields) == TrancheLevel.ENRICHED

    def test_full_when_all_nine(self):
        all_names = MANDATORY_FIELD_NAMES + OPTIONAL_FIELD_NAMES
        assert evaluate_tranche_level(all_names) == TrancheLevel.FULL

    def test_tranche_percentages(self):
        assert TRANCHE_PERCENTAGES[TrancheLevel.INCOMPLETE] == 0
        assert TRANCHE_PERCENTAGES[TrancheLevel.BASIC] == 40
        assert TRANCHE_PERCENTAGES[TrancheLevel.ENRICHED] == 70
        assert TRANCHE_PERCENTAGES[TrancheLevel.FULL] == 100


class TestEvaluateTranchesFunction:
    def test_full_xapi_returns_full_tranche(self):
        result = evaluate_tranches([FULL_XAPI])
        assert result["tranche_level"] == "full"
        assert result["percentage"] == 100
        assert result["total_passed"] == 9
        assert result["total_failed"] == 0
        assert len(result["mandatory_passed"]) == 6
        assert len(result["optional_passed"]) == 3

    def test_minimal_xapi_returns_basic_tranche(self):
        result = evaluate_tranches([MINIMAL_XAPI])
        assert result["tranche_level"] == "basic"
        assert result["percentage"] == 40
        assert len(result["mandatory_passed"]) == 6
        assert len(result["mandatory_failed"]) == 0
        assert len(result["optional_passed"]) == 0
        assert len(result["optional_failed"]) == 3

    def test_missing_actor_returns_incomplete(self):
        result = evaluate_tranches([NO_ACTOR])
        assert result["tranche_level"] == "incomplete"
        assert result["percentage"] == 0
        assert "actor" in result["mandatory_failed"]

    def test_empty_statement_returns_incomplete(self):
        result = evaluate_tranches([{"statement": {}}])
        assert result["tranche_level"] == "incomplete"
        assert result["percentage"] == 0

    def test_single_dict_input_works(self):
        result = evaluate_tranches(FULL_XAPI)
        assert result["tranche_level"] == "full"

    def test_per_item_results_structure(self):
        result = evaluate_tranches([FULL_XAPI, MINIMAL_XAPI])
        assert len(result["per_item"]) == 2
        assert result["per_item"][0]["item_index"] == 0
        assert result["per_item"][1]["item_index"] == 1
        assert "fields" in result["per_item"][0]