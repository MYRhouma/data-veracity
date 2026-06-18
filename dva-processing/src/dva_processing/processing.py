import json
from typing import Any

import psycopg as pg

from .config import PG_PASS, PG_URL, PG_USER
from .eval import eval_requirement
from .log import get_logger
from .model import (
    AoVGenerationRequest,
    AoVGenerationRequestPayload,
    AoVRequest,
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


def handle_aov_request(request: AoVRequest) -> AoVGenerationRequest:
    logger.debug("Handling an AoV request", request=request)
    contract: dict[str, Any] = request.contract

    if "vla" not in contract or "schema" not in contract["vla"]:
        logger.warning("No VLA in contract or no requirements in VLA; ignoring")
        return None

    # Evaluate all requirements
    results: list[EvaluationResult] = []
    any_evaluations = False
    if len(contract["vla"]["schema"]) == 0:
        logger.warning("No schema items found in VLA")
    for schema_item in contract["vla"]["schema"]:
        if "quality" not in schema_item:
            continue

        requirement_dict: dict
        for requirement_dict in schema_item["quality"]:
            any_evaluations = True
            try:
                requirement = Requirement(**requirement_dict)
                result: EvaluationResult = eval_requirement(request.data, requirement)
            except Exception as e:
                logger.warning(
                    "An error was thrown the evaluation of a requirement; tolerating",
                    error=e,
                )
                result = EvaluationResult(
                    engine=None, timestamp=now(), success=False, error=str(e)
                )
            finally:
                results.append(result)

    if not any_evaluations:
        logger.warning("Nothing was evaluated from this VLA")

    all_success: bool = all(x.success for x in results)

    # Log evaluation results to psql database
    try:
        with pg.connect(f"{PG_URL}?user={PG_USER}&password={PG_PASS}") as conn:
            conn.execute(
                """
            UPDATE request_logs
            SET
              evaluation_passing = %s,
              evaluation_date = %s,
              evaluation_results = %s
            WHERE request_id = %s
            """,
                (
                    all_success,
                    now().isoformat(),
                    json.dumps([r.model_dump_json() for r in results]),
                    request.id,
                ),
            )
        logger.info(
            f"Successfully updated PostgreSQL entry for request {request.id}",
            overall_result=all_success,
            request_id=request.id,
        )
    except Exception as e:
        logger.error(
            f"Failed to update request log entry for request {request.id}", error=e
        )

    # Return AoV generation request for ACA-Py
    return AoVGenerationRequest(
        request_id=request.id,
        exchange_id=request.exchangeID,
        contract_id=contract["id"],
        subject=contract["dataProvider"],
        issuer_id=request.attesterID,
        payload=AoVGenerationRequestPayload(
            success=all_success,
            results=results,
        ),
        target="self",
    )
