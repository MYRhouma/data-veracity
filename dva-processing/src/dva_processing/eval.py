import json
from typing import Any

from great_expectations.core import ExpectationValidationResult
from open_data_contract_standard.model import DataQuality

from .engines import great_expectations as ge
from .engines import jq
from .engines import json_schema as schema
from .log import get_logger
from .model import (
    EvaluationResult,
    GreatExpectationParams,
    JQResult,
    JSONSchemaValidationResult,
    QualityEngine,
)
from .util import extract_df, now

logger = get_logger()


class UnknownEngineError(ValueError):
    """A requirement names an engine this service cannot run."""

    def __init__(self, engine: str | None) -> None:
        self.engine = engine
        super().__init__(f"Unknown quality engine {engine}")


def parse_engine(engine: str | None) -> QualityEngine:
    """Resolve an ODCS ``DataQuality.engine`` to an engine we implement.

    ODCS types ``engine`` as a free-form string, so a requirement naming an
    unsupported engine deserialises happily; this is where it is caught.
    """
    try:
        return QualityEngine(engine)
    except ValueError as e:
        logger.error(f"Unknown quality engine {engine}", engine=engine)
        raise UnknownEngineError(engine) from e


def eval_requirement(data: Any, requirement: DataQuality) -> EvaluationResult:
    match parse_engine(requirement.engine):
        case QualityEngine.great_expectations:
            res = eval_requirement_ge(data, requirement)
        case QualityEngine.schema:
            res = eval_requirement_schema(data, requirement)
        case QualityEngine.jq:
            res = eval_requirement_jq(data, requirement)
        case engine:  # unreachable while every engine above is handled
            raise UnknownEngineError(engine)
    logger.info(f"Result of requirement evaluation: {res.success}", result=res)
    return res


def eval_requirement_ge(data: Any, requirement: DataQuality) -> EvaluationResult:
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


def eval_requirement_schema(data: Any, requirement: DataQuality) -> EvaluationResult:
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


def eval_requirement_jq(data: Any, requirement: DataQuality) -> EvaluationResult:
    logger.debug("Evaluating JQ expression requirement")
    results: list[JQResult] = jq.eval_expression(data, requirement.implementation)
    # A jq expression yields one JQResult per output value, so the
    # requirement only holds if every one of them does.
    success = all(r.success for r in results)
    logger.debug(f"JQ expression evaluation success: {success}", details=results)
    return EvaluationResult(
        engine=requirement.engine,
        timestamp=now(),
        success=success,
        details=json.dumps([r.model_dump() for r in results]),
    )
