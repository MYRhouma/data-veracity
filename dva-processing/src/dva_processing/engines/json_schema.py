import html
import ipaddress
import json
from typing import Any
from urllib.parse import urlparse

import requests
import validators
from jsonschema import ValidationError, validate as jsvalidate

from ..model import JSONSchemaValidationResult

ALLOWED_SCHEMES = {"https"}
BLOCKED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]
SCHEMA_FETCH_TIMEOUT = 10


def _is_url_safe(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ALLOWED_SCHEMES:
        return False
    hostname = parsed.hostname
    if not hostname:
        return False
    try:
        resolved = ipaddress.ip_address(hostname)
        return not any(resolved in net for net in BLOCKED_NETWORKS)
    except ValueError:
        return True


def validate(data: Any, schema: str) -> JSONSchemaValidationResult:
    if validators.url(schema):
        if not _is_url_safe(schema):
            return JSONSchemaValidationResult(
                success=False,
                errors="Schema URL is not allowed: only HTTPS URLs to public hosts are permitted",
            )
        try:
            resp = requests.get(schema, timeout=SCHEMA_FETCH_TIMEOUT)
            resp.raise_for_status()
            schema = resp.json()
        except requests.RequestException as e:
            return JSONSchemaValidationResult(success=False, errors=f"Failed to fetch schema: {e}")
    else:
        schema = json.loads(html.unescape(schema))

    try:
        jsvalidate(instance=data, schema=schema)
    except ValidationError as e:
        return JSONSchemaValidationResult(success=False, errors=str(e))

    return JSONSchemaValidationResult(success=True, errors=None)