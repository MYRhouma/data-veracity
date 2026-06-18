import json
import pytest

from dva_processing.engines.jq import eval_expression, _validate_expression


def test_jq_basic_valid():
    data = {"statement": {"actor": {"name": "John", "objectType": "Agent"}}}
    query = 'if (.statement.actor != null and .statement.actor.name != null) then {success: true, details: "actor present"} else {success: false, details: "no actor"} end'
    results = eval_expression(data, query)
    assert len(results) == 1
    assert results[0].success is True
    assert "actor present" in results[0].details


def test_jq_env_blocked():
    with pytest.raises(ValueError, match="forbidden token"):
        _validate_expression("env.DVA_POSTGRES_PASSWORD")


def test_jq_input_blocked():
    with pytest.raises(ValueError, match="forbidden token"):
        _validate_expression("input")


def test_jq_while_blocked():
    with pytest.raises(ValueError, match="forbidden token"):
        _validate_expression("while(true; . + 1)")


def test_jq_reduce_safe():
    _validate_expression("reduce range(5) as $x (0; . + $x)")


def test_jq_dollar_env_blocked():
    with pytest.raises(ValueError, match="forbidden token"):
        _validate_expression("$ENV")


def test_jq_debug_blocked():
    with pytest.raises(ValueError, match="forbidden token"):
        _validate_expression("debug")


def test_jq_stderr_blocked():
    with pytest.raises(ValueError, match="forbidden token"):
        _validate_expression("stderr")


def test_jq_inputs_blocked():
    with pytest.raises(ValueError, match="forbidden token"):
        _validate_expression("inputs")


def test_jq_recurse_safe():
    _validate_expression("recurse")


def test_jq_foreach_safe():
    _validate_expression("foreach")


def test_jq_safe_expression_passes():
    _validate_expression('if (.statement.actor != null) then {success: true} else {success: false} end')
    _validate_expression(".statement.actor.name")
    _validate_expression('.statement | keys')
    _validate_expression('map(select(.success == true))')


def test_jq_eval_actor_check():
    data = {
        "statement": {
            "actor": {
                "objectType": "Agent",
                "account": {"homePage": "https://lms.example.com", "name": "user123"},
            }
        }
    }
    query = 'if (.statement.actor != null and .statement.actor.objectType != null and .statement.actor.account != null and .statement.actor.account.homePage != null and .statement.actor.account.name != null) then {success: true, details: "all actor fields present"} else {success: false, details: "missing actor fields"} end'
    results = eval_expression(data, query)
    assert results[0].success is True

    bad_data = {"statement": {"actor": None}}
    results = eval_expression(bad_data, query)
    assert results[0].success is False