import os

from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, PlainTextResponse, Response

from .log import get_logger
from .model import (
    EvaluateBatchRequest,
    EvaluationFromTemplateRequest,
    EvaluationResult,
)
from .processing import (
    EvaluationRequest,
    handle_eval_batch_request,
    handle_eval_request,
    handle_eval_from_template_request,
)

logger = get_logger()

_SWAGGER_UI_HTML = """\
<!DOCTYPE html>
<html>
  <head>
    <title>DVA Processing — Swagger UI</title>
    <link href="https://unpkg.com/swagger-ui-dist@5.17.12/swagger-ui.css" rel="stylesheet">
    <link href="https://unpkg.com/swagger-ui-dist@5.17.12/favicon-32x32.png" rel="icon" type="image/x-icon">
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.17.12/swagger-ui-bundle.js" crossorigin="anonymous"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.17.12/swagger-ui-standalone-preset.js" crossorigin="anonymous"></script>
    <script>
      window.onload = function() {
        SwaggerUIBundle({
          url: '/swagger/openapi.yaml',
          dom_id: '#swagger-ui',
          deepLinking: false,
          presets: [SwaggerUIBundle.presets.apis, SwaggerUIStandalonePreset],
          layout: 'StandaloneLayout'
        });
      };
    </script>
  </body>
</html>
"""

app = FastAPI(
    # Disable auto-generated docs — hand-written spec is served at /swagger
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.get("/swagger", response_class=HTMLResponse, include_in_schema=False)
def swagger_ui() -> HTMLResponse:
    """Serve the Swagger UI loaded from the hand-written OpenAPI spec."""
    return HTMLResponse(content=_SWAGGER_UI_HTML)


@app.get("/swagger/openapi.yaml", response_class=PlainTextResponse, include_in_schema=False)
def swagger_spec() -> PlainTextResponse:
    """Serve the hand-written OpenAPI spec YAML from disk."""
    spec_path = os.environ.get("DVA_PROCESSING_OPENAPI_FILE", "/app/openapi.yaml")
    try:
        with open(spec_path, "r", encoding="utf-8") as fh:
            content = fh.read()
    except FileNotFoundError:
        return PlainTextResponse(content="# spec file not found", status_code=404)
    return PlainTextResponse(content=content, media_type="application/yaml")


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


@app.post("/evaluate-batch", response_model=list[EvaluationResult])
def process_batch(request: EvaluateBatchRequest):
    """Veracity checks in the synchronous attestation flow.

    Called by the DVA API with the full VLA document (as retrieved from
    the VLA Manager API during VLA resolution) and the original data.
    Returns one :class:`EvaluationResult` per requirement in
    ``vla.schema[*].quality[*]``.
    """
    logger.info(
        "Received batch evaluation request",
        vla_keys=list((request.vla or {}).keys()),
    )
    return handle_eval_batch_request(request)


@app.post("/evaluate/from-template", response_model=EvaluationResult)
def process_from_template(request: EvaluationFromTemplateRequest, response: Response):
    """Data-Intermediary-only endpoint used while authoring VLAs.

    Fetches the template from the VLA Manager API, renders it with the
    provided model (Handlebars ``{{var}}`` syntax), then evaluates the
    resulting requirement against ``data``.
    """
    logger.info("Received evaluate-from-template request", template_id=request.template_id)
    result = handle_eval_from_template_request(request)
    if result.error is not None:
        logger.warning("Error during evaluate-from-template", error=result.error)
    return result


@app.exception_handler(RequestValidationError)
def handle_validation_exception(request, err):
    logger.error("Validation error during request processing", error=err)
    return Response(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT)
