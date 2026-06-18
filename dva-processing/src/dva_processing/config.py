from os import environ as env

from pydantic import BaseModel

# RabbitMQ queue name for AoV requests
QUEUE_NAME = "ATTESTATION_REQUESTS"

# RabbitMQ server hostname
RABBITMQ_HOST = env.get("DVA_RABBITMQ_HOST", default="localhost")

# Postgres connection data
PG_URL = env.get("DVA_POSTGRES_URL", default="postgresql://localhost:5432")
PG_USER = env.get("DVA_POSTGRES_USER", default="postgres")
PG_PASS = env.get("DVA_POSTGRES_PASSWORD", default="postgres")

# Log level (must be supported by structlog)
LOG_LEVEL = env.get("DVA_LOG_LEVEL", default="warn")

# ACA-Py Controller URL
ACA_PY_CONTROLLER_URL = env.get("DVA_ACA_PY_CONTROLLER_URL", default="localhost:8050")


class Configuration(BaseModel):
    log_level: str = LOG_LEVEL


cfg = Configuration()
