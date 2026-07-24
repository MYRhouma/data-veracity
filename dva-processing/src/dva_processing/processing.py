from .eval import eval_requirement
from .log import get_logger
from .model import (
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