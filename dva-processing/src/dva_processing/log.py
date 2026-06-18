from sys import stderr

import structlog
from structlog import make_filtering_bound_logger
from structlog.dev import ConsoleRenderer
from structlog.processors import JSONRenderer, StackInfoRenderer, TimeStamper
from structlog.stdlib import add_log_level

import dva_processing.config


def setup_logging():
    shared_processors = [
        add_log_level,
        StackInfoRenderer(),
        TimeStamper(fmt="iso"),
    ]

    if stderr.isatty():
        processors = shared_processors + [ConsoleRenderer()]
    else:
        processors = shared_processors + [JSONRenderer()]

    structlog.configure(
        processors=processors,
        context_class=dict,
        wrapper_class=make_filtering_bound_logger(dva_processing.config.cfg.log_level),
    )


def get_logger():
    return structlog.get_logger()
