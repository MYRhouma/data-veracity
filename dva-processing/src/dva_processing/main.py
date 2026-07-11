import uvicorn

import dva_processing.config
import dva_processing.http
import dva_processing.log


def main(verbose=False, debug=False):
    if debug:
        dva_processing.config.cfg.log_level = "debug"
    elif verbose:
        dva_processing.config.cfg.log_level = "info"
    dva_processing.log.setup_logging()
    logger = dva_processing.log.get_logger()

    logger.info("Starting DVA PROCESSING (HTTP only — no RabbitMQ)")
    uvicorn.run(
        dva_processing.http.app,
        host="0.0.0.0",
        port=5000,
        log_level="info",
    )


def cli():
    main()