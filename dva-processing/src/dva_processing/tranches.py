"""
Tranche evaluation: runs all 9 xAPI field checks against the data
and returns a tranche-level result (incomplete/basic/enriched/full).
"""

import json
from typing import Any

from .engines.jq import eval_expression
from .log import get_logger
from .model import EvaluationResult
from .util import now
from .xapi_checks import (
    XAPI_FIELD_CHECKS,
    MANDATORY_FIELD_NAMES,
    OPTIONAL_FIELD_NAMES,
    TRANCHE_PERCENTAGES,
    TrancheLevel,
    evaluate_tranche_level,
)

logger = get_logger()


def evaluate_tranches(data: Any) -> dict[str, Any]:
    if not isinstance(data, list):
        data = [data]

    all_field_results: dict[str, bool] = {}
    per_item_results: list[dict[str, Any]] = []

    for idx, item in enumerate(data):
        item_field_status: dict[str, bool] = {}
        for check in XAPI_FIELD_CHECKS:
            try:
                results = eval_expression(item, check.jq_expression)
                passed = all(r.success for r in results) if results else False
            except Exception as e:
                logger.warning(
                    "JQ field check failed",
                    field=check.name,
                    error=str(e),
                    item_index=idx,
                )
                passed = False
            item_field_status[check.name] = passed
            all_field_results[check.name] = passed

        per_item_results.append({
            "item_index": idx,
            "fields": item_field_status,
        })

    passed_fields = [name for name, ok in all_field_results.items() if ok]
    failed_fields = [name for name, ok in all_field_results.items() if not ok]

    tranche = evaluate_tranche_level(passed_fields)
    percentage = TRANCHE_PERCENTAGES[tranche]

    mandatory_passed = [f for f in passed_fields if f in MANDATORY_FIELD_NAMES]
    optional_passed = [f for f in passed_fields if f in OPTIONAL_FIELD_NAMES]

    return {
        "tranche_level": tranche.value,
        "percentage": percentage,
        "mandatory_passed": mandatory_passed,
        "mandatory_failed": [f for f in MANDATORY_FIELD_NAMES if f not in mandatory_passed],
        "optional_passed": optional_passed,
        "optional_failed": [f for f in OPTIONAL_FIELD_NAMES if f not in optional_passed],
        "total_passed": len(passed_fields),
        "total_failed": len(failed_fields),
        "per_item": per_item_results,
    }