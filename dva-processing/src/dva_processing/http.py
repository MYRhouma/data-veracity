from fastapi import FastAPI, status
from fastapi.responses import Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from .errors import http_exception_handler, unknown_engine_handler
from .eval import UnknownEngineError
from .log import get_logger
from .model import EvaluationResult
from .processing import EvaluationRequest, handle_eval_request

logger = get_logger()
app = FastAPI()

# Render errors as the spec's {type, title} rather than FastAPI's {detail}.
# Body validation keeps FastAPI's own 422, which the spec documents separately.
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(UnknownEngineError, unknown_engine_handler)


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
