from datetime import datetime, timezone
from unittest.mock import patch

from dva_processing.model import (
    AoVGenerationRequest,
    AoVGenerationRequestPayload,
    EvaluationResult,
    QualityEngine,
)
from dva_processing.rmq_consumer import forward_aov_generation


def _make_gen_request() -> AoVGenerationRequest:
    return AoVGenerationRequest(
        request_id="test-001",
        exchange_id="xchg-001",
        contract_id="contract-001",
        subject="did:web:provider",
        issuer_id="attester-001",
        payload=AoVGenerationRequestPayload(
            success=True,
            results=[
                EvaluationResult(
                    engine=QualityEngine.jq,
                    timestamp=datetime.now(timezone.utc),
                    success=True,
                )
            ],
        ),
        target="self",
    )


@patch("dva_processing.rmq_consumer.requests.post")
@patch("dva_processing.rmq_consumer.DVA_ISSUER", "jws")
def test_dva_issuer_jws_skips_acapy_forward(mock_post):
    """When DVA_ISSUER=jws, the /generate_aov POST to ACA-Py must be skipped."""
    forward_aov_generation(_make_gen_request())
    mock_post.assert_not_called()


@patch("dva_processing.rmq_consumer.requests.post")
@patch("dva_processing.rmq_consumer.DVA_ISSUER", "acapy")
def test_dva_issuer_acapy_still_calls_acapy(mock_post):
    """When DVA_ISSUER=acapy (default), the /generate_aov POST to ACA-Py must happen."""
    forward_aov_generation(_make_gen_request())
    mock_post.assert_called_once()
    called_url = mock_post.call_args.args[0]
    assert "/generate_aov" in called_url, f"expected /generate_aov in URL, got {called_url}"
