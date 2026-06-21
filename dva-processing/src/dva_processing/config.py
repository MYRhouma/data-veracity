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

# ACA-Py Controller URL (legacy, kept for backward compatibility)
ACA_PY_CONTROLLER_URL = env.get("DVA_ACA_PY_CONTROLLER_URL", default="localhost:8050")

# VC Issuer URL (replaces ACA-Py controller for W3C VC + JWS)
VC_ISSUER_URL = env.get("DVA_VC_ISSUER_URL", default="http://localhost:8050")

# Which VC backend to use: "vc_issuer" (new W3C JWS) or "acapy" (legacy)
VC_BACKEND = env.get("DVA_VC_BACKEND", default="vc_issuer")

# API key for VC issuer
DVA_API_KEY = env.get("DVA_API_KEY", default="changeme")


class Configuration(BaseModel):
    log_level: str = LOG_LEVEL


cfg = Configuration()
