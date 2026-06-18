import json
from typing import Any

from great_expectations.core import ExpectationValidationResult

from .engines import great_expectations as ge
from .engines import jq
from .engines import json_schema as schema
from .log import get_logger
from .model import (
    EvaluationResult,
    JQResult,
    JSONSchemaValidationResult,
    QualityEngine,
    Requirement,
    GreatExpectationParams,
)
from .util import extract_df, now

logger = get_logger()


def eval_requirement(data: Any, requirement: Requirement) -> EvaluationResult:
    match requirement.engine:
        case QualityEngine.great_expectations:
            res = eval_requirement_ge(data, requirement)
        case QualityEngine.schema:
            res = eval_requirement_schema(data, requirement)
        case QualityEngine.jq:
            res = eval_requirement_jq(data, requirement)
        case _:
            logger.error(
                f"Unknown quality engine {requirement.engine}",
                engine=requirement.engine,
            )
            raise ValueError("Unknown quality engine")
    logger.info(f"Result of requirement evaluation: {res.success}", result=res)
    return res


def eval_requirement_ge(data: Any, requirement: Requirement) -> EvaluationResult:
    logger.debug("Evaluating requirement using Great Expectations")

    ge_params: GreatExpectationParams = ge.parse_implementation(
        requirement.implementation
    )
    logger.debug("Deserialized GE parameters", parameters=ge_params)

    data_df = extract_df(data, ge_params.meta.schema)
    logger.debug("Mapped JSON to dataframe", dataframe=data_df)

    results: ExpectationValidationResult = ge.validate_expectation(data_df, ge_params)
    success = results.get("success", False)
    logger.debug(
        f"GreatExpectations expectation validation successful: {success}",
        details=results,
    )

    return EvaluationResult(
        engine=requirement.engine,
        timestamp=now(),
        success=success,
        details=json.dumps(results.to_json_dict()),
    )


def eval_requirement_schema(data: Any, requirement: Requirement) -> EvaluationResult:
    logger.debug("Evaluating JSON schema conformance requirement")
    result: JSONSchemaValidationResult = schema.validate(
        data, requirement.implementation
    )
    logger.debug(f"JSON schema evaluation success: {result.success}", details=result)
    return EvaluationResult(
        engine=requirement.engine,
        timestamp=now(),
        success=result.success,
        details=result.errors,
    )


def eval_requirement_jq(data: Any, requirement: Requirement) -> EvaluationResult:
    logger.debug("Evaluating JQ expression requirement")
    results: list[JQResult] = jq.eval_expression(data, requirement.implementation)
    logger.debug(
        f"JQ expression evaluation success: {results.success}", details=results
    )
    return EvaluationResult(
        engine=requirement.engine,
        timestamp=now(),
        success=all(r.success for r in results),
        details=json.dumps(results),
    )
