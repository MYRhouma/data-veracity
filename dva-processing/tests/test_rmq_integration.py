import json
from unittest.mock import patch, MagicMock
from dva_processing.rmq_consumer import run
from dva_processing.model import AoVRequest


def test_config_has_vc_backend():
    from dva_processing.config import VC_BACKEND, VC_ISSUER_URL
    assert VC_BACKEND in ("vc_issuer", "acapy")
    assert VC_ISSUER_URL is not None


def test_rmq_consumer_uses_vc_issuer_url():
    from dva_processing.config import VC_ISSUER_URL, VC_BACKEND
    assert VC_BACKEND == "vc_issuer"
    assert "8050" in VC_ISSUER_URL or "localhost" in VC_ISSUER_URL