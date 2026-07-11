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


def handle_eval_batch_request(request: EvaluateBatchRequest) -> list[EvaluationResult]:
    """Evaluate every requirement in a VLA's ``schema[*].quality[*]``.

    This is the veracity-checks phase of the synchronous attestation
    flow. The DVA API calls ``POST /evaluate-batch`` with the full VLA
    document (retrieved from the VLA Manager API) and the raw data; the
    processing service returns one :class:`EvaluationResult` per
    requirement.

    Pure function — no Postgres write. The DVA API owns the RequestLog
    audit row.
    """
    vla: dict[str, Any] = request.vla or {}
    schema_items = vla.get("schema") or []
    if not isinstance(schema_items, list):
        logger.warning("VLA schema is not a list; treating as empty")
        schema_items = []

    results: list[EvaluationResult] = []
    any_evaluations = False
    for schema_item in schema_items:
        if not isinstance(schema_item, dict):
            continue
        quality = schema_item.get("quality") or []
        if not isinstance(quality, list):
            continue
        for requirement_dict in quality:
            any_evaluations = True
            try:
                requirement = Requirement(**requirement_dict)
                result = eval_requirement(request.data, requirement)
            except Exception as e:
                logger.warning(
                    "An error was thrown during evaluation of a requirement; tolerating",
                    error=e,
                )
                result = EvaluationResult(
                    engine=None, timestamp=now(), success=False, error=str(e)
                )
            results.append(result)

    if not any_evaluations:
        logger.warning("Nothing was evaluated from this VLA")

    return results