from dva_processing.eval import eval_requirement
from dva_processing.model import EvaluationResult, QualityEngine, Requirement


def test_eval_ge_column_values_between():
    requirement = Requirement(
        engine=QualityEngine.great_expectations,
        implementation="""
type: ExpectColumnValuesToBeBetween
kwargs:
  column: registered
  min_value: '2025-01-01T00:00:00Z'
  max_value: '2026-01-01T00:00:00Z'
meta:
  schema:
    columns:
      registered:
        dtype: datetime
""",
    )

    data_passing = {
        "name": "John Smith",
        "registered": "2025-01-04T13:12:11Z",
        "age": 32,
    }
    data_failing = {
        "name": "Jane Smith",
        "registered": "2022-02-12T23:00:44Z",
        "age": 19,
    }

    result: EvaluationResult = eval_requirement(data_passing, requirement)
    assert result.success

    result: EvaluationResult = eval_requirement(data_failing, requirement)
    assert not result.success


def test_eval_ge_column_length_between():
    requirement = Requirement(
        engine=QualityEngine.great_expectations,
        implementation="""
type: ExpectColumnValueLengthsToBeBetween
kwargs:
  column: synopsis
  min_value: 100
meta:
  schema:
    columns:
      synopsis:
      details:
""",
    )

    data_passing = {
        "synopsis": "This synopsis quite long. " * 200,
        "details": "...",
    }
    data_failing = {"synopsis": "tooshort", "details": "..."}

    result: EvaluationResult = eval_requirement(data_passing, requirement)
    assert result.success

    result: EvaluationResult = eval_requirement(data_failing, requirement)
    assert not result.success
