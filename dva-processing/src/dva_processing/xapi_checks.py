"""
Predefined JQ expressions for checking xAPI statement field compliance.

9 fields total:
  Mandatory (6): actor, verb, object_id, object_definition, timestamp, context
  Optional  (3): result, context_extensions, object_extensions

Tranche allocation:
  0%  — 0 fields present (incomplete)
  40% — 6 mandatory fields present (basic)
  70% — 6 mandatory + at least 2 optional (enriched)
  100% — all 9 fields present (full)
"""

from dataclasses import dataclass
from enum import StrEnum


class TrancheLevel(StrEnum):
    INCOMPLETE = "incomplete"
    BASIC = "basic"
    ENRICHED = "enriched"
    FULL = "full"


@dataclass
class XapiFieldCheck:
    name: str
    mandatory: bool
    jq_expression: str
    description: str


XAPI_FIELD_CHECKS: list[XapiFieldCheck] = [
    XapiFieldCheck(
        name="actor",
        mandatory=True,
        description="Actor must be present with either mbox or account",
        jq_expression=(
            'if .statement.actor != null and '
            '(.statement.actor.mbox != null or '
            ' (.statement.actor.account != null and '
            '  .statement.actor.account.name != null and '
            '  .statement.actor.account.homePage != null)) '
            'then {success: true, details: "Actor present and valid"} '
            'else {success: false, details: "Actor missing or invalid"} end'
        ),
    ),
    XapiFieldCheck(
        name="verb",
        mandatory=True,
        description="Verb must be present with a valid IRI id",
        jq_expression=(
            'if .statement.verb != null and .statement.verb.id != null '
            'and (.statement.verb.id | startswith("http")) '
            'then {success: true, details: "Verb present with valid IRI"} '
            'else {success: false, details: "Verb missing or invalid IRI"} end'
        ),
    ),
    XapiFieldCheck(
        name="object_id",
        mandatory=True,
        description="Object must be present with a valid IRI id",
        jq_expression=(
            'if .statement.object != null and .statement.object.id != null '
            'and (.statement.object.id | startswith("http")) '
            'then {success: true, details: "Object ID present and valid"} '
            'else {success: false, details: "Object ID missing or invalid"} end'
        ),
    ),
    XapiFieldCheck(
        name="object_definition",
        mandatory=True,
        description="Object definition must be present with a type IRI",
        jq_expression=(
            'if .statement.object != null and .statement.object.definition != null '
            'and .statement.object.definition.type != null '
            'and (.statement.object.definition.type | startswith("http")) '
            'then {success: true, details: "Object definition present with type IRI"} '
            'else {success: false, details: "Object definition missing or no type IRI"} end'
        ),
    ),
    XapiFieldCheck(
        name="timestamp",
        mandatory=True,
        description="Timestamp must be present and ISO-8601 formatted",
        jq_expression=(
            'if .statement.timestamp != null and (.statement.timestamp | type) == "string" '
            'and (.statement.timestamp | length) > 10 '
            'then {success: true, details: "Timestamp present and formatted"} '
            'else {success: false, details: "Timestamp missing or malformed"} end'
        ),
    ),
    XapiFieldCheck(
        name="context",
        mandatory=True,
        description="Context must be present (language or contextActivities)",
        jq_expression=(
            'if .statement.context != null and '
            '(.statement.context.language != null or '
            ' .statement.context.contextActivities != null) '
            'then {success: true, details: "Context present"} '
            'else {success: false, details: "Context missing or empty"} end'
        ),
    ),
    XapiFieldCheck(
        name="result",
        mandatory=False,
        description="Result must be present with score or response",
        jq_expression=(
            'if .statement.result != null and '
            '(.statement.result.score != null or '
            ' .statement.result.response != null) '
            'then {success: true, details: "Result present with score or response"} '
            'else {success: false, details: "Result missing or incomplete"} end'
        ),
    ),
    XapiFieldCheck(
        name="context_extensions",
        mandatory=False,
        description="Context extensions must be present with at least one key",
        jq_expression=(
            'if .statement.context != null and .statement.context.extensions != null '
            'and (.statement.context.extensions | keys | length) > 0 '
            'then {success: true, details: "Context extensions present"} '
            'else {success: false, details: "Context extensions missing or empty"} end'
        ),
    ),
    XapiFieldCheck(
        name="object_extensions",
        mandatory=False,
        description="Object definition extensions must be present with at least one key",
        jq_expression=(
            'if .statement.object != null and .statement.object.definition != null '
            'and .statement.object.definition.extensions != null '
            'and (.statement.object.definition.extensions | keys | length) > 0 '
            'then {success: true, details: "Object extensions present"} '
            'else {success: false, details: "Object extensions missing or empty"} end'
        ),
    ),
]


MANDATORY_FIELDS = [c for c in XAPI_FIELD_CHECKS if c.mandatory]
OPTIONAL_FIELDS = [c for c in XAPI_FIELD_CHECKS if not c.mandatory]
ALL_FIELD_NAMES = [c.name for c in XAPI_FIELD_CHECKS]
MANDATORY_FIELD_NAMES = [c.name for c in MANDATORY_FIELDS]
OPTIONAL_FIELD_NAMES = [c.name for c in OPTIONAL_FIELDS]

MANDATORY_COUNT = len(MANDATORY_FIELDS)
OPTIONAL_COUNT = len(OPTIONAL_FIELDS)
TOTAL_COUNT = len(XAPI_FIELD_CHECKS)


def evaluate_tranche_level(passed_field_names: list[str]) -> TrancheLevel:
    mandatory_passed = [f for f in passed_field_names if f in MANDATORY_FIELD_NAMES]
    optional_passed = [f for f in passed_field_names if f in OPTIONAL_FIELD_NAMES]

    if len(mandatory_passed) < MANDATORY_COUNT:
        return TrancheLevel.INCOMPLETE
    if len(optional_passed) == OPTIONAL_COUNT:
        return TrancheLevel.FULL
    if len(optional_passed) >= 2:
        return TrancheLevel.ENRICHED
    return TrancheLevel.BASIC


TRANCHE_PERCENTAGES = {
    TrancheLevel.INCOMPLETE: 0,
    TrancheLevel.BASIC: 40,
    TrancheLevel.ENRICHED: 70,
    TrancheLevel.FULL: 100,
}