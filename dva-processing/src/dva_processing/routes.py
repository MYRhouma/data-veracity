"""
FastAPI routes for the DVA Processing module.

* ``POST /evaluate`` — evaluate a single requirement against data.  Useful
  for trying a requirement out while building a VLA.
* ``POST /evaluate-batch`` — evaluate every requirement in a VLA against
  data.  Called by the DVA API during the synchronous attestation flow.
* ``POST /evaluate/from-template`` — fetch a VLA template from the VLA
  Manager, render it with a model, and evaluate the result against data.
"""

from fastapi import APIRouter, Response, status

from .errors import http_error
from .log import get_logger
from .model import (
    EvaluateBatchRequest,
    EvaluationFromTemplateRequest,
    EvaluationRequest,
    EvaluationResult,
)
from .processing import (
    handle_eval_batch_request,
    handle_eval_from_template_request,
    handle_eval_request,
)
from .templates import TemplateRenderError
from .vla_manager import TemplateNotFoundError, VLAManagerError

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


@router.post("/evaluate/from-template", response_model=EvaluationResult)
def evaluate_from_template(
    request: EvaluationFromTemplateRequest, response: Response
) -> EvaluationResult:
    logger.info(
        "Received evaluate-from-template request", template_id=request.template_id
    )
    try:
        result = handle_eval_from_template_request(request)
    except TemplateNotFoundError as e:
        raise http_error(
            status.HTTP_404_NOT_FOUND, "No template with the given ID exists"
        ) from e
    except VLAManagerError as e:
        raise http_error(
            status.HTTP_502_BAD_GATEWAY, "VLA Manager API unavailable", detail=str(e)
        ) from e
    except TemplateRenderError as e:
        raise http_error(
            status.HTTP_400_BAD_REQUEST, "Failed to render template", detail=str(e)
        ) from e

    if result.error is not None:
        logger.warning("Error during evaluate-from-template", error=result.error)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    return result
