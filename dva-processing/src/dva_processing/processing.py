from typing import Any

from .eval import eval_requirement
from .log import get_logger
from .model import (
    EvaluateBatchRequest,
    EvaluationRequest,
    EvaluationResult,
    Requirement,
)
from .util import now

logger = get_logger()


def handle_eval_request(request: EvaluationRequest) -> EvaluationResult:
    logger.debug("Handling an evaluation request", request=request)
    try:
        return eval_requirement(request.data, request.requirement)
    except Exception as e:
        return EvaluationResult(
            engine=request.requirement.engine,
            timestamp=now(),
            success=False,
            details=None,
            error=str(e),
        )


def _eval_one(data: Any, requirement_dict: dict[str, Any]) -> EvaluationResult:
    """Evaluate one requirement dict, tolerating errors."""
    try:
        requirement = Requirement(**requirement_dict)
        return eval_requirement(data, requirement)
    except Exception as e:
        logger.warning(
            "An error was thrown during evaluation of a requirement; tolerating",
            error=e,
        )
        return EvaluationResult(
            engine=None, timestamp=now(), success=False, error=str(e)
        )


def handle_eval_batch_request(request: EvaluateBatchRequest) -> list[EvaluationResult]:
    """Evaluate every requirement in a VLA.

    Supports three VLA shapes encountered across the codebase:
      1. ``vla.schema`` as a list, each entry containing a ``quality``
         list (canonical ODCS shape — ``schema: [{quality:[…]}]``)
      2. ``vla.schema`` as a single dict containing a ``quality`` list
         (ODCS dict shape — ``schema: {quality:[…]}``)
      3. ``vla.quality`` as a top-level list (flat VLAs with no schema
         subdivision — ``quality: […]``)

    Pure function — no Postgres write. The DVA API owns the RequestLog
    audit row.
    """
    vla: dict[str, Any] = request.vla or {}

    # Normalize schema into a list of schema items
    schema_items: list[Any] = []
    raw_schema = vla.get("schema")
    if isinstance(raw_schema, list):
        schema_items = raw_schema
    elif isinstance(raw_schema, dict):
        schema_items = [raw_schema]
    # else: no schema; we'll still check top-level quality below

    results: list[EvaluationResult] = []
    any_evaluations = False

    # Iterate the schema items (each is a dict with a "quality" list)
    for schema_item in schema_items:
        if not isinstance(schema_item, dict):
            continue
        quality = schema_item.get("quality") or []
        if not isinstance(quality, list):
            continue
        for requirement_dict in quality:
            any_evaluations = True
            results.append(_eval_one(request.data, requirement_dict))

    # Fallback: if no schema, try top-level quality list
    if not any_evaluations:
        top_quality = vla.get("quality")
        if isinstance(top_quality, list):
            for requirement_dict in top_quality:
                any_evaluations = True
                results.append(_eval_one(request.data, requirement_dict))
        elif isinstance(top_quality, dict):
            any_evaluations = True
            results.append(_eval_one(request.data, top_quality))

    if not any_evaluations:
        logger.warning("Nothing was evaluated from this VLA")

    return results