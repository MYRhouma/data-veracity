from collections.abc import Generator
from time import sleep

import requests
import structlog
from pika import BasicProperties, BlockingConnection, ConnectionParameters
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic

from .config import ACA_PY_CONTROLLER_URL, DVA_ISSUER, QUEUE_NAME, RABBITMQ_HOST
from .log import get_logger
from .model import AoVGenerationRequest, AoVRequest
from .processing import handle_aov_request

logger: structlog.BoundLogger = get_logger()


def run() -> None:
    conn: BlockingConnection = connect_with_retry(
        ConnectionParameters(host=RABBITMQ_HOST, heartbeat=60)
    )
    chan: BlockingChannel = conn.channel()
    chan.queue_declare(queue=QUEUE_NAME)

    def callback(
        chan: BlockingChannel,
        method: Basic.Deliver,
        props: BasicProperties,
        body: bytes,
    ) -> None:
        aov_request = AoVRequest.model_validate_json(
            bytearray(body).decode(encoding="utf-8")
        )
        logger.info("Received AoV request via RMQ", request=aov_request)

        aov_gen_request: AoVGenerationRequest = handle_aov_request(aov_request)
        if aov_gen_request is None or not aov_gen_request.payload.success:
            logger.warning("Not all checks were successful; not sending to ACA-Py")
            return

        forward_aov_generation(aov_gen_request)

    chan.basic_consume(queue=QUEUE_NAME, auto_ack=True, on_message_callback=callback)
    logger.info("Waiting for RMQ messages")
    chan.start_consuming()


def forward_aov_generation(aov_gen_request: AoVGenerationRequest) -> None:
    """Forward the AoV generation request to the configured issuer.

    When DVA_ISSUER=='jws', the dva-api sync /attestation endpoint already
    returned the signed JWS to the caller, so the ACA-Py /generate_aov forward
    is skipped entirely. When DVA_ISSUER=='acapy' (default, legacy), the
    request is POSTed to the ACA-Py controller as before.
    """
    if DVA_ISSUER == "jws":
        logger.info("DVA_ISSUER=jws: skipping ACA-Py /generate_aov forward")
        return
    logger.info("Sending AoV VC generation request to ACA-Py", request=aov_gen_request)
    requests.post(
        f"{ACA_PY_CONTROLLER_URL}/generate_aov",
        json=aov_gen_request.model_dump(mode="json"),
    )


def connect_with_retry(
    params: ConnectionParameters,
    max_retries: int = -1,
    initial_delay_s: float = 1,
    max_delay_s: float = 60,
    backoff_multiplier: float = 2.0,
) -> BlockingConnection:
    delay: float = initial_delay_s
    attempt: int
    for attempt in range_or_infinity(max_retries):
        try:
            logger.debug(
                f"Connecting to RabbitMQ at {params.host}:{params.port}; attempt {attempt + 1}"
            )
            return BlockingConnection(params)
        except Exception as e:
            logger.error(f"Connection attempt failed: {type(e).__name__}", error=e)

            if max_retries != -1 and attempt >= max_retries:
                logger.error(
                    f"Unable to connect to RabbitMQ at {params.host} after {max_retries} attempts"
                )
                raise e

            logger.debug(f"Retrying RMQ connection in {delay}s")
            sleep(delay)

            delay = min(delay * backoff_multiplier, max_delay_s)


def range_or_infinity(n: int) -> Generator[int, None, None]:
    if n == -1:
        i = 0
        while True:
            yield i
            i = i + 1
    else:
        yield from range(n)
