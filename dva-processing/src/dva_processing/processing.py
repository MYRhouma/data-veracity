from typing import Any

from open_data_contract_standard.model import DataQuality

from .eval import eval_requirement, parse_engine
from .log import get_logger
from .model import EvaluateBatchRequest, EvaluationRequest, EvaluationResult
from .util import now

logger = get_logger()


def _evaluate(data: Any, requirement: DataQuality) -> EvaluationResult:
    """
    Evaluate one requirement, reporting an engine failure as a result.

    An unusable engine is deliberately *not* caught here: there would be no
    engine to report, and the fault is the request's, so it surfaces as a
    ``400`` rather than as a failed check.
    """
    engine = parse_engine(requirement.engine)
    try:
        return eval_requirement(data, requirement)
    except Exception as e:
        logger.warning("Requirement evaluation failed", error=e)
        return EvaluationResult(
            engine=engine,
            timestamp=now(),
            success=False,
            details=None,
            error=str(e),
        )


def handle_eval_request(request: EvaluationRequest) -> EvaluationResult:
    logger.debug("Handling an evaluation request", request=request)
    return _evaluate(request.data, request.requirement)


def handle_eval_batch_request(request: EvaluateBatchRequest) -> list[EvaluationResult]:
    logger.debug("Handling a batch evaluation request", request=request)
    results = [
        _evaluate(request.data, requirement)
        for schema_object in request.vla.schema_ or []
        for requirement in schema_object.quality or []
    ]
    if not results:
        logger.warning("Nothing was evaluated from this VLA")
    return results
