from os import environ as env

from pydantic import BaseModel

LOG_LEVEL = env.get("DVA_LOG_LEVEL", default="warn")


class Configuration(BaseModel):
    log_level: str = LOG_LEVEL


cfg = Configuration()