import html
import json
from typing import Any

from jsonschema import ValidationError, validate as jsvalidate

from ..model import JSONSchemaValidationResult


def validate(data: Any, schema: str) -> JSONSchemaValidationResult:
    # TODO: Do we want to allow loading from arbitrary URL?
    # TODO: Can we eliminate this unescape?
    schema = json.loads(html.unescape(schema))

    try:
        jsvalidate(instance=data, schema=schema)
    except ValidationError as e:
        return JSONSchemaValidationResult(success=False, errors=e)

    return JSONSchemaValidationResult(success=True, errors=None)
