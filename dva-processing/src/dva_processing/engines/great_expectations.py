import pandas as pd
from great_expectations import expectations, get_context
from great_expectations.core import ExpectationValidationResult
from great_expectations.data_context.types.base import ProgressBarsConfig
from pydantic_yaml import parse_yaml_raw_as

from ..model import GreatExpectationParams


def parse_implementation(implementation_yaml: str) -> GreatExpectationParams:
    return parse_yaml_raw_as(GreatExpectationParams, implementation_yaml)


def validate_expectation(
    df: pd.DataFrame, params: GreatExpectationParams
) -> ExpectationValidationResult:
    ctx = get_context(mode="ephemeral")
    # Disable progress bars; they pollute the logs
    ctx.variables.progress_bars = ProgressBarsConfig(globally=False)

    data_src = ctx.data_sources.add_pandas(name="request")
    data_asset = data_src.add_dataframe_asset(name="request_df")
    batch_def = data_asset.add_batch_definition_whole_dataframe(name="whole_df")
    batch_params = {"dataframe": df}

    gx_func = getattr(expectations, params.type)
    expectation = gx_func(**params.kwargs)

    batch = batch_def.get_batch(batch_parameters=batch_params)
    return batch.validate(expectation)
