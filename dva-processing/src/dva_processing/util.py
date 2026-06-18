import pandas as pd

from datetime import datetime, timezone
from jsonpath_ng import parse as jp_parse

from .model import JSONToDFSchema


def now() -> datetime:
    return datetime.now(timezone.utc)


def extract_df(data: dict, schema: JSONToDFSchema) -> pd.DataFrame:
    root_path = schema.root_path
    root_expr = jp_parse(root_path)
    root_matches = root_expr.find(data)

    if len(root_matches) == 0:
        raise ValueError(f"No data found in JSON data at root path {root_path}")

    records = root_matches[0].value
    if not isinstance(records, list):
        records = [records]

    df_dict = {}
    for col_name, col_spec in schema.columns.items():
        col_path = col_spec.jsonpath.lstrip("$.")

        vals = []
        for rec in records:
            val = rec
            for part in col_path.split("."):
                if isinstance(val, dict):
                    val = val.get(part)
                else:
                    val = None
            vals.append(val)

        df_dict[col_name] = vals

    df = pd.DataFrame(df_dict)

    for col_name, col_spec in schema.columns.items():
        match col_spec.dtype:
            case "string":
                df[col_name] = df[col_name].astype(str)
            case "int":
                df[col_name] = pd.to_numeric(df[col_name], errors="coerce").astype(
                    "Int64"
                )
            case "float":
                df[col_name] = pd.to_numeric(df[col_name], errors="coerce")
            case "datetime":
                df[col_name] = pd.to_datetime(df[col_name], errors="coerce")
            case "bool":
                df[col_name] = df[col_name].astype(bool)

    return df
