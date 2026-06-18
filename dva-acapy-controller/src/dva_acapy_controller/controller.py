import requests
import json

from psycopg_pool import AsyncConnectionPool
from asyncio import Queue, CancelledError
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel
from time import sleep
from typing import Dict, Any
from uuid import uuid4

from .config import (
    ADMIN_LABEL,
    ADMIN_URL,
    LOG_FILE,
    PEER_LABEL,
    POSTGRES_URL,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
)


class AOV(BaseModel):
    vc_id: str
    valid_since: datetime
    subject: str
    issuer_id: str
    record_id: str
    contract_id: str
    data_exchange_id: str
    payload: str


class AOVRequest(BaseModel):
    request_id: str
    exchange_id: str
    contract_id: str
    subject: str
    issuer_id: str
    payload: Dict[str, Any]
    target: str = "self"


class AoVPresentationRequest(BaseModel):
    dataExchangeId: str
    attesterLabel: str
    attesterAgentURL: str


@asynccontextmanager
async def lifespan(app):
    print(f"{ADMIN_LABEL} Controller is starting...")
    await presentation_queue.put({"message": "Startup test data!"})
    print("Starting self initialization...")
    await init_all_self()
    print("Self init done!")
    global pool
    pool = AsyncConnectionPool(
        conninfo=POSTGRES_URL,
        kwargs=dict(user=POSTGRES_USER, password=POSTGRES_PASSWORD),
        min_size=2,
        max_size=10,
    )
    pool.open()

    yield

    print(f"{ADMIN_LABEL} Controller is shutting down...")
    pool.close()
    if webhook_logs:
        with open("log_human_readable.json", "w") as f:
            json.dump(webhook_logs, f, indent=2)


pool: AsyncConnectionPool

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

webhook_logs = []
presentation_queue = Queue()

SELF_CONNECTION_ID = None
SELF_SCHEMA_ID = None
SELF_CRED_DEF_ID = None


@app.get("/", response_class=HTMLResponse)
async def root():
    html = Path("static/index.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html)


# Helper function: wait until connection is active
def wait_until_connection_active(admin_url, conn_id, timeout=10):
    for _ in range(timeout):
        conns = requests.get(f"{admin_url}/connections").json()["results"]
        conn = next((c for c in conns if c["connection_id"] == conn_id), None)
        if conn and conn["state"] == "active":
            return True
        sleep(1)
    return False


@app.post("/webhooks/topic/{topic}/")
async def webhook_listener(topic: str, request: Request):
    data = await request.json()
    data["source"] = ADMIN_LABEL
    webhook_logs.append({"topic": topic, "data": data})
    with open(LOG_FILE, "w") as f:
        json.dump(webhook_logs, f, indent=2)
    await presentation_queue.put(data)
    print(f"Webhook received on topic: {topic}")
    return {"status": "received"}


@app.get("/connections/self")
async def get_self_connection():
    global SELF_CONNECTION_ID
    if not SELF_CONNECTION_ID:
        return {"error": "Self-connection not initialized."}
    return {"self_connection_id": SELF_CONNECTION_ID}


@app.post("/init_all_self")
async def init_all_self():
    global SELF_CONNECTION_ID, SELF_SCHEMA_ID, SELF_CRED_DEF_ID

    # Step 1: Create Invitation for self-connection
    invitation_resp = requests.post(
        f"{ADMIN_URL}/out-of-band/create-invitation",
        json={
            "handshake_protocols": ["https://didcomm.org/didexchange/1.0"],
            "use_public_did": False,
        },
    )
    if invitation_resp.status_code != 200:
        return {
            "error": "Failed to create self-invitation",
            "details": invitation_resp.text,
        }

    invitation = invitation_resp.json()["invitation"]

    # Step 2: Receive own invitation
    receive_resp = requests.post(
        f"{ADMIN_URL}/out-of-band/receive-invitation",
        json=invitation,
    )
    if receive_resp.status_code != 200:
        return {
            "error": "Failed to accept own invitation",
            "details": receive_resp.text,
        }

    conn_id = receive_resp.json()["connection_id"]

    # Step 3: Wait until connection is active
    if not wait_until_connection_active(f"{ADMIN_URL}/", conn_id):
        return {"error": "Self connection did not become active"}

    SELF_CONNECTION_ID = conn_id

    # Step 4: Create Self-Identity Schema
    schema_resp = requests.post(
        f"{ADMIN_URL}/schemas",
        json={
            "schema_name": f"Self-Identity-{uuid4().hex[:6]}",
            "schema_version": "1.0",
            "attributes": [
                "vc_id",
                "valid_since",
                "subject",
                "issuer_id",
                "record_id",
                "contract_id",
                "data_exchange_id",
                "payload",
            ],
        },
    )
    if schema_resp.status_code != 200:
        return {
            "error": "Failed to create Self-Identity schema",
            "details": schema_resp.text,
        }

    SELF_SCHEMA_ID = schema_resp.json().get("schema_id")

    # Step 5: Create Credential Definition
    cred_def_resp = requests.post(
        f"{ADMIN_URL}/credential-definitions",
        json={
            "schema_id": SELF_SCHEMA_ID,
            "support_revocation": False,
            "tag": "self-identity",
        },
    )
    if cred_def_resp.status_code != 200:
        return {
            "error": "Failed to create Self-Identity credential definition",
            "details": cred_def_resp.text,
        }

    SELF_CRED_DEF_ID = cred_def_resp.json().get("credential_definition_id")

    with open("cred_def.json", "w") as f:
        json.dump({"cred_def_id": SELF_CRED_DEF_ID}, f)

    # Step 6: Self-Issue Credential to Own Wallet
    cred_attrs = {
        "vc_id": str(uuid4()),
        "valid_since": datetime.utcnow().isoformat(),
        "subject": "Provider Subject",
        "issuer_id": "Provider",
        "record_id": str(uuid4()),
        "contract_id": "contract123",
        "data_exchange_id": "xchg123",
        "payload": "[]",
    }

    issue_payload = {
        "connection_id": SELF_CONNECTION_ID,
        "credential_preview": {
            "@type": "issue-credential/2.0/credential-preview",
            "attributes": [{"name": k, "value": v} for k, v in cred_attrs.items()],
        },
        "filter": {"indy": {"cred_def_id": SELF_CRED_DEF_ID}},
    }

    issue_resp = requests.post(
        f"{ADMIN_URL}/issue-credential-2.0/send-offer", json=issue_payload
    )
    if issue_resp.status_code != 200:
        return {
            "error": "Failed to self-issue credential",
            "details": issue_resp.text,
        }

    return {
        "message": "Self-connection, schema, credential definition, and self-credential issued successfully.",
        "self_connection_id": SELF_CONNECTION_ID,
        "self_schema_id": SELF_SCHEMA_ID,
        "self_cred_def_id": SELF_CRED_DEF_ID,
    }


@app.post("/generate_aov")
async def generate_aov(payload: AOVRequest):
    global SELF_CONNECTION_ID, SELF_CRED_DEF_ID

    record = AOV(
        vc_id=str(uuid4()),
        valid_since=datetime.utcnow(),
        subject=payload.subject,
        issuer_id=payload.issuer_id,
        record_id=str(uuid4()),
        contract_id=payload.contract_id,
        data_exchange_id=payload.exchange_id,
        payload=json.dumps(payload.payload),
    )

    target = payload.target
    if target not in ["self", PEER_LABEL]:
        raise HTTPException(status_code=400, detail="Invalid target")

    if target == "self":
        if not SELF_CONNECTION_ID or not SELF_CRED_DEF_ID:
            raise HTTPException(
                status_code=400,
                detail="Self connection or credential definition not initialized",
            )
        connection_id = SELF_CONNECTION_ID
        cred_def_id = SELF_CRED_DEF_ID
    else:
        conns = requests.get(f"{ADMIN_URL}/connections").json()["results"]
        peer_conn = next(
            (c for c in conns if c["connection_id"] != SELF_CONNECTION_ID),
            None,
        )
        if not peer_conn:
            raise HTTPException(
                status_code=400, detail=f"No {PEER_LABEL} connection found"
            )
        connection_id = peer_conn["connection_id"]

        try:
            with open("cred_def.json", "r") as f:
                cred_def_data = json.load(f)
            cred_def_id = cred_def_data["cred_def_id"]
        except Exception:
            raise HTTPException(
                status_code=500, detail="Missing or invalid credential definition file"
            )

    cred_attrs = {
        "vc_id": record.vc_id,
        "valid_since": record.valid_since.isoformat(),
        "subject": record.subject,
        "issuer_id": record.issuer_id,
        "record_id": record.record_id,
        "contract_id": record.contract_id,
        "data_exchange_id": record.data_exchange_id,
        "payload": record.payload,
    }

    issue_payload = {
        "connection_id": connection_id,
        "credential_preview": {
            "@type": "issue-credential/2.0/credential-preview",
            "attributes": [{"name": k, "value": v} for k, v in cred_attrs.items()],
        },
        "filter": {"indy": {"cred_def_id": cred_def_id}},
    }

    issue_resp = requests.post(
        f"{ADMIN_URL}/issue-credential-2.0/send", json=issue_payload
    )
    print(f"Issue response: {issue_resp}")

    if issue_resp.status_code != 200:
        return {"error": "Credential issue failed", "details": issue_resp.text}

    async with pool.connection() as conn:
        cur = await conn.execute(
            """
            UPDATE request_logs
            SET vc_issued_date = %s, vc_id = %s
            WHERE request_id = %s
            """,
            (datetime.utcnow(), record.vc_id, payload.request_id),
        )
        match cur.rowcount:
            case 0:
                print("Did not update any PostgreSQL table rows; this is likely a bug")
            case 1:
                print(
                    f"Successfully updated PostgreSQL table row for {payload.request_id}"
                )
            case _:
                print(
                    f"Updated more than one PostgreSQL table rows for {payload.request_id}; this is likely a bug"
                )

    return {"message": f"AOV issued to {target}", "credential_data": cred_attrs}


@app.post("/request_presentation_from_peer")
async def request_presentation_from_peer(payload: AoVPresentationRequest):
    create_inv_resp = requests.post(
        f"{ADMIN_URL}/out-of-band/create-invitation",
        json={
            "handshake_protocols": ["https://didcomm.org/didexchange/1.0"],
            "use_public_did": False,
        },
    )
    if create_inv_resp.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail="Failed to create OOB invitation for attester",
        )

    invitation = create_inv_resp.json().get("invitation")
    if not invitation:
        raise HTTPException(
            status_code=500,
            detail="Failed to create OOB invitation for attester",
        )

    receive_inv_resp = requests.post(
        f"{payload.attesterAgentURL}/out-of-band/receive-invitation",
        json=invitation,
    )
    if receive_inv_resp.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail="Failed to send invitation OOB invitation to attester",
        )

    is_active = False
    for _ in range(15):
        conns = requests.get(f"{ADMIN_URL}/connections").json().get("results", [])
        attester_conn = next(
            (
                c
                for c in conns
                if c["state"] == "active"
                and c.get("their_label", "").lower() == payload.attesterLabel
            ),
            None,
        )
        if attester_conn:
            is_active = True
            break
        sleep(1)

    if not is_active:
        raise HTTPException(
            status_code=500,
            detail="Connection to attester timed out",
        )

    pres_request = {
        "connection_id": attester_conn.get("connection_id"),
        "presentation_request": {
            "indy": {
                "name": "AoVPresentationRequest",
                "version": "1.0",
                "requested_attributes": {
                    "attr_subject": {"name": "subject", "restrictions": [{}]},
                    "attr_issuer_id": {"name": "issuer_id", "restrictions": [{}]},
                    "attr_vc_id": {"name": "vc_id", "restrictions": [{}]},
                    "attr_valid_since": {"name": "valid_since", "restrictions": [{}]},
                    "attr_record_id": {"name": "record_id", "restrictions": [{}]},
                    "attr_contract_id": {"name": "contract_id", "restrictions": [{}]},
                    "attr_data_exchange_id": {
                        "name": "data_exchange_id",
                        "restrictions": [
                            {"attr::data_exchange_id::value": payload.dataExchangeId},
                        ],
                    },
                    "attr_payload": {"name": "payload", "restrictions": [{}]},
                },
                "requested_predicates": {},
            },
        },
    }

    resp = requests.post(
        f"{ADMIN_URL}/present-proof-2.0/send-request",
        json=pres_request,
    )
    if resp.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail="Failed to send AoV presentation request to attester",
        )
    resp.raise_for_status()
    data = resp.json()

    return {
        "message": "Presentation request sent to attester",
        "aov": data,
    }


@app.get("/events/")
async def events():
    async def event_generator():
        while True:
            try:
                event = await presentation_queue.get()
                event_source = event.get("source")
                if event_source is None:
                    event_source = ADMIN_LABEL
                yield f"data: {json.dumps(event)}\n\n"
            except CancelledError:
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")
