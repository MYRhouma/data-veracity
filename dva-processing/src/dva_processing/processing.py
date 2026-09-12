from .eval import eval_requirement, parse_engine
from .log import get_logger
from .model import EvaluationRequest, EvaluationResult
from .util import now

logger = get_logger()


def handle_eval_request(request: EvaluationRequest) -> EvaluationResult:
    logger.debug("Handling an evaluation request", request=request)
    # Resolve the engine up front: an unusable one is a bad request rather
    # than a failed evaluation, and there would be no engine to report.
    engine = parse_engine(request.requirement.engine)
    try:
        return eval_requirement(request.data, request.requirement)
    except Exception as e:
        return EvaluationResult(
            engine=engine,
            timestamp=now(),
            success=False,
            details=None,
            error=str(e),
        )
