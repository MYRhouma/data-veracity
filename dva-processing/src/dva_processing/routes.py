"""
FastAPI routes for the DVA Processing module.

* ``POST /evaluate`` — evaluate a single requirement against data.  Useful
  for trying a requirement out while building a VLA.
"""

from fastapi import APIRouter, Response, status

from .log import get_logger
from .model import EvaluationRequest, EvaluationResult
from .processing import handle_eval_request

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
