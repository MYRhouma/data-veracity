from os import environ as env

from pydantic import BaseModel

# Log level (must be supported by structlog)
LOG_LEVEL = env.get("DVA_LOG_LEVEL", default="warn")

# Postgres connection data — only used by the legacy async path
# (handle_aov_request). The new sync path (handle_eval_batch_request)
# is stateless and does not touch the DB.
PG_URL = env.get("DVA_POSTGRES_URL", default="postgresql://localhost:5432")
PG_USER = env.get("DVA_POSTGRES_USER", default="postgres")
PG_PASS = env.get("DVA_POSTGRES_PASSWORD", default="postgres")


class Configuration(BaseModel):
    log_level: str = LOG_LEVEL


cfg = Configuration()