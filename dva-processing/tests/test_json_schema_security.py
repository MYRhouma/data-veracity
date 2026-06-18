import pytest
import json

from dva_processing.engines.json_schema import validate, _is_url_safe


def test_ssrf_blocks_http_scheme():
    assert _is_url_safe("http://example.com/schema.json") is False


def test_ssrf_blocks_localhost():
    assert _is_url_safe("https://127.0.0.1/schema.json") is False
    assert _is_url_safe("https://localhost/schema.json") is True  # hostname, not IP


def test_ssrf_blocks_private_ip_10():
    assert _is_url_safe("https://10.0.0.1/schema.json") is False


def test_ssrf_blocks_private_ip_172():
    assert _is_url_safe("https://172.16.0.1/schema.json") is False


def test_ssrf_blocks_private_ip_192():
    assert _is_url_safe("https://192.168.1.1/schema.json") is False


def test_ssrf_blocks_link_local():
    assert _is_url_safe("https://169.254.169.254/latest/meta-data/") is False


def test_ssrf_blocks_ipv6_loopback():
    assert _is_url_safe("https://[::1]/schema.json") is False


def test_ssrf_allows_public_https():
    assert _is_url_safe("https://schema.example.com/schema.json") is True


def test_ssrf_blocks_no_scheme():
    assert _is_url_safe("schema.json") is False


def test_ssrf_blocks_empty_url():
    assert _is_url_safe("") is False


def test_inline_schema_still_works():
    schema = json.dumps({
        "type": "object",
        "properties": {
            "name": {"type": "string"},
        },
        "required": ["name"],
    })
    data_valid = {"name": "John"}
    data_invalid = {"age": 30}

    result = validate(data_valid, schema)
    assert result.success is True

    result = validate(data_invalid, schema)
    assert result.success is False


def test_inline_schema_html_unescaped():
    schema = '{&quot;type&quot;: &quot;object&quot;, &quot;properties&quot;: {&quot;name&quot;: {&quot;type&quot;: &quot;string&quot;}}, &quot;required&quot;: [&quot;name&quot;]}'
    data_valid = {"name": "John"}
    result = validate(data_valid, schema)
    assert result.success is True