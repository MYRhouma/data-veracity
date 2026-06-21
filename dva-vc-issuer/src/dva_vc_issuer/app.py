import json
from datetime import datetime, timezone
from contextlib import asynccontextmanager

import psycopg
import structlog
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .config import (
    DVA_API_KEY,
    DVA_POSTGRES_URL,
    DVA_POSTGRES_USER,
    DVA_POSTGRES_PASSWORD,
)
from .keys import load_or_create_key_pair
from .models import AoVRequest, VerifyRequest
from .signing import create_vc, verify_vc, get_did_document

structlog.configure()
logger = structlog.get_logger()

_private_key = None


def get_private_key():
    global _private_key
    if _private_key is None:
        _private_key = load_or_create_key_pair()
    return _private_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _private_key
    logger.info("dva-vc-issuer starting up...")
    _private_key = load_or_create_key_pair()
    logger.info("RSA key pair loaded", key_id="key-1")
    yield
    logger.info("dva-vc-issuer shutting down...")


app = FastAPI(
    title="DVA VC Issuer",
    description="W3C Verifiable Credential issuer with JWS signing",
    version="0.1.0",
    lifespan=lifespan,
)


def _check_api_key(x_api_key: str | None = Header(default=None)):
    if x_api_key != DVA_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


@app.post("/generate_aov")
async def generate_aov(
    request: AoVRequest,
    x_api_key: str | None = Header(default=None),
):
    _check_api_key(x_api_key)

    logger.info("Generating AoV VC", request_id=request.request_id)
    vc = create_vc(request.model_dump(), get_private_key())

    try:
        with psycopg.connect(
            f"{DVA_POSTGRES_URL}?user={DVA_POSTGRES_USER}&password={DVA_POSTGRES_PASSWORD}"
        ) as conn:
            conn.execute(
                """
                UPDATE request_logs
                SET vc_issued_date = %s, vc_id = %s
                WHERE request_id = %s
                """,
                (datetime.now(timezone.utc), vc["id"], request.request_id),
            )
            conn.commit()
        logger.info("Updated PostgreSQL record", request_id=request.request_id, vc_id=vc["id"])
    except Exception as e:
        logger.error("Failed to update PostgreSQL", error=str(e))

    return {"message": f"AoV VC issued", "vc": vc}


@app.post("/verify")
async def verify(
    request: VerifyRequest,
    x_api_key: str | None = Header(default=None),
):
    _check_api_key(x_api_key)

    valid, error = verify_vc(request.vc, get_private_key())
    return {"valid": valid, "error": error}


@app.get("/.well-known/did.json")
async def did_document():
    return get_did_document(get_private_key())


@app.get("/health")
async def health():
    return {"status": "ok", "service": "dva-vc-issuer", "time": datetime.now(timezone.utc).isoformat()}