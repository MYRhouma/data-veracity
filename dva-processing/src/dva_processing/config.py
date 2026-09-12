from os import environ as env

from pydantic import BaseModel

# Postgres connection data
PG_URL = env.get("DVA_POSTGRES_URL", default="postgresql://localhost:5432")
PG_USER = env.get("DVA_POSTGRES_USER", default="postgres")
PG_PASS = env.get("DVA_POSTGRES_PASSWORD", default="postgres")

# Hand-written OpenAPI spec served at /swagger.
# Missing → fall back to FastAPI's auto-generated schema.
OPENAPI_FILE = env.get("DVA_PROCESSING_OPENAPI_FILE", default="/app/openapi.yaml")

# Log level (must be supported by structlog)
LOG_LEVEL = env.get("DVA_LOG_LEVEL", default="warn")


class Configuration(BaseModel):
    log_level: str = LOG_LEVEL


cfg = Configuration()
