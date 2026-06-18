from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import Response

from .log import get_logger
from .model import EvaluationResult
from .processing import EvaluationRequest, handle_eval_request

logger = get_logger()
app = FastAPI()


@app.post("/evaluate")
def process_request(
    request: EvaluationRequest, response: Response, response_model=EvaluationResult
):
    logger.info("Received evaluation request", request=request)
    result: EvaluationResult = handle_eval_request(request)
    if result.error is not None:
        logger.warning("Error during evaluation", error=result.error)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    return result


@app.exception_handler(RequestValidationError)
def handle_validation_exception(
    request: EvaluationRequest,
    err: RequestValidationError,
    response: Response,
):
    logger.error("Validation error during request processing", error=err)
    response.status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
