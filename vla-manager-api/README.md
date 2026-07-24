# VLA Manager API

VLA Manager API is a FastAPI service hosted at the **Data Intermediary** that owns the
Veracity Level Agreements (VLAs) on behalf of all participants.

## Why

In the refactored DVA topology this is the **only** place VLAs live. Each participant's
DVA API no longer stores VLAs in its own Postgres — instead, during the synchronous
attestation flow, the DVA API calls `GET /vla/{id}` over HTTP on this service
to resolve a VLA from its ID.

Separating VLA ownership from the attestation gateway means:
- DVA API shrinks to pure orchestration (HTTP gateway; one role)
- VLAs are authored once and shared across participants
- The VLA Manager Vue UI talks to a single dedicated backend

## Role

| Endpoint | Persona | Purpose |
|---|---|---|
| `GET /vla` | VLA Manager UI, admin | List all VLAs |
| `GET /vla/{id}` | DVA API, UI | Retrieve a VLA by its UUID — used during VLA resolution in the synchronous attestation flow |
| `POST /vla` | VLA Manager UI | Create a VLA from a partial ODCS payload |
| `POST /vla/from-templates` | VLA Manager UI | *Reserved (501)* — implemented in a later refactor step |
| `DELETE /vla` | Admin only | Wipe all VLAs (guarded by `VLA_MANAGER_API_KEY` bearer auth; disabled when key is empty) |

This service intentionally does **not** do evaluation, attestation, or credential issuance —
those are concerns of `dva-processing` and the `dva-vc-manager` respectively.

## Run locally (dev)

```bash
cd data-veracity-main/vla-manager-api
uv sync
uv run pytest                # tests (FakeVLARepo, no Postgres needed)
uv run vla-manager-api        # boot the gateway on :8000
```

## Run in docker-compose

See `test-env/compose.yml` — the service is wired as `vla-manager-api` on port `9099`
(Data Intermediary) with `VLA_MANAGER_DB_URL=postgresql://postgres-vla:5432/vla`.

## Configuration (.env)

| Var | Default | Purpose |
|---|---|---|
| `VLA_MANAGER_DB_URL` | *(empty)* | Postgres DSN, e.g. `postgresql://vla:vla@postgres:5432/vla` |
| `VLA_MANAGER_API_KEY` | *(empty)* | Shared-secret bearer for `DELETE /vla`. When empty, the endpoint is disabled. |
| `VLA_MANAGER_API_PORT` | `8000` | Listen port |
| `VLA_MANAGER_API_LOG_LEVEL` | `INFO` | Standard Python log-level name |