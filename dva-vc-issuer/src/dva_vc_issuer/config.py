from os import environ as env


DVA_VC_HOST = env.get("DVA_VC_HOST", default="0.0.0.0")
DVA_VC_PORT = int(env.get("DVA_VC_PORT", default="8050"))

DVA_VC_DID_DOMAIN = env.get("DVA_VC_DID_DOMAIN", default="localhost")
DVA_VC_KEY_PATH = env.get("DVA_VC_KEY_PATH", default="data/keys/private_key.pem")
DVA_VC_KEY_ID = env.get("DVA_VC_KEY_ID", default="key-1")

DVA_VC_ISSUER_ID = env.get("DVA_VC_ISSUER_ID", default="dva-vc-issuer")

DVA_POSTGRES_URL = env.get("DVA_POSTGRES_URL", default="postgresql://localhost:5432/dva")
DVA_POSTGRES_USER = env.get("DVA_POSTGRES_USER", default="postgres")
DVA_POSTGRES_PASSWORD = env.get("DVA_POSTGRES_PASSWORD", default="postgres")

DVA_LOG_LEVEL = env.get("DVA_LOG_LEVEL", default="info")
DVA_API_KEY = env.get("DVA_API_KEY", default="changeme")