"""
FastAPI routes for the DVA Processing module.

* ``POST /evaluate`` — evaluate a single requirement against data.  Useful
  for trying a requirement out while building a VLA.
* ``POST /evaluate-batch`` — evaluate every requirement in a VLA against
  data.  Called by the DVA API during the synchronous attestation flow.
"""

from fastapi import APIRouter, Response, status

from .log import get_logger
from .model import EvaluateBatchRequest, EvaluationRequest, EvaluationResult
from .processing import handle_eval_batch_request, handle_eval_request

logger = get_logger()

router = APIRouter(tags=["Evaluation"])


@router.post("/evaluate", response_model=EvaluationResult)
def evaluate(request: EvaluationRequest, response: Response) -> EvaluationResult:
    logger.info("Received evaluation request", request=request)
    result: EvaluationResult = handle_eval_request(request)
    if result.error is not None:
        logger.warning("Error during evaluation", error=result.error)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    return result


@router.post("/evaluate-batch", response_model=list[EvaluationResult])
def evaluate_batch(request: EvaluateBatchRequest) -> list[EvaluationResult]:
    # Always a 200: a requirement the engine could not run is reported as a
    # failed result of its own, so callers see every check they asked for.
    logger.info("Received batch evaluation request", request=request)
    return handle_eval_batch_request(request)
