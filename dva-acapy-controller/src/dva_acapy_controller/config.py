from os import environ as env


ADMIN_URL = env.get("ADMIN_URL")
ADMIN_LABEL = env.get("ADMIN_LABEL")

PEER_AGENT_URL = env.get("PEER_AGENT_URL")
PEER_CONTROLLER_URL = env.get("PEER_CONTROLLER_URL")
PEER_CONTROLLER_PORT_IN = env.get("PEER_CONTROLLER_PORT_IN")
PEER_CONTROLLER_PORT_OUT = env.get("PEER_CONTROLLER_PORT_OUT")
PEER_LABEL = env.get("PEER_LABEL")

POSTGRES_URL = env.get("DVA_POSTGRES_URL", default="postgresql://localhost:5432/dva")
POSTGRES_USER = env.get("DVA_POSTGRES_USER", default="postgres")
POSTGRES_PASSWORD = env.get("DVA_POSTGRES_PASSWORD", default="postgres")

LOG_FILE = "log.json"
