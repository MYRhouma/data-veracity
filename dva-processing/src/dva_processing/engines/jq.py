import signal
from typing import Any

import jq

from ..model import JQResult

JQ_DANGEROUS_TOKENS = [
    "$ENV",
    "__loc__",
    "ascii_downcase",
    "ascii_upcase",
    "builtins",
    "debug",
    "drem",
    "env",
    "halt",
    "halt_error",
    "infinite",
    "input",
    "inputs",
    "isnan",
    "isinfinite",
    "j0",
    "j1",
    "lgamma",
    "limit",
    "nan",
    "nearbyint",
    "smap",
    "stderr",
    "tgamma",
    "while",
    "until",
    "y0",
    "y1",
]

JQ_TIMEOUT_SECONDS = 5


class _TimeoutError(Exception):
    pass


def _jq_timeout_handler(signum, frame):
    raise _TimeoutError("JQ expression evaluation timed out")


def _validate_expression(query_str: str) -> None:
    normalized = query_str.lower().replace(" ", "").replace("\t", "").replace("\n", "")
    for token in JQ_DANGEROUS_TOKENS:
        token_lower = token.lower()
        if token_lower in normalized:
            raise ValueError(f"JQ expression contains forbidden token: {token}")


def eval_expression(data: Any, query_str: str) -> list[JQResult]:
    _validate_expression(query_str)

    old_handler = signal.signal(signal.SIGALRM, _jq_timeout_handler)
    signal.alarm(JQ_TIMEOUT_SECONDS)
    try:
        query: jq._Program = jq.compile(query_str)
        results = [JQResult(**x) for x in query.input(data)]
    except _TimeoutError:
        raise ValueError(f"JQ expression evaluation timed out after {JQ_TIMEOUT_SECONDS}s")
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

    return results