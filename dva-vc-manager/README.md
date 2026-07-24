# DVA VC Manager

DVA VC Manager is a FastAPI service hosted at each **Participant** that owns the
Attestation-of-Veracity credential lifecycle:

* **Issues** AoV credentials as W3C VC 2.0 JSON-LD JWS (Ed25519/EdDSA) at the provider side.
* **Verifies** AoV JWS credentials at the consumer side against a local ``did:key`` whitelist.

## Why

In the refactored DVA topology this is the only component that performs cryptographic signing
or verification of credentials. Stepping the JWS issuance out of ``dva-api`` lets the API
shrink to pure orchestration while reusing a single, audited crypto library (**PyNaCl** /
libsodium — no hand-rolled cryptography anywhere).

## Role

| Endpoint | Persona | Purpose |
|---|---|---|
| ``POST /aov/issue`` | DVA API (provider side) | Credential issuance — sign the AoV JWS during the synchronous attestation flow |
| ``POST /aov/verify`` | DVA API (consumer side) | Verify a JWS against the attester whitelist (fail-closed) |
| ``GET /admin/whitelist`` | Operator | List trusted attester ``did:key`` identifiers |
| ``POST /admin/whitelist`` | Operator | Register a trusted attester ``did:key`` |
| ``DELETE /admin/whitelist/{did_key}`` | Operator | Remove a trusted attester |
| ``GET /admin/keys`` | Operator | View this service's own issuer ``did:key`` (read-only) |

All ``/admin/*`` endpoints require ``Authorization: Bearer ${DVA_VC_MANAGER_API_KEY}`` and
fail-closed with ``401`` when the key is empty.

## Cryptography libraries

| Concern | Library | Reason |
|---|---|---|
| Ed25519 sign/verify | ``PyNaCl`` (libsodium binding) | Canonical, audited, no hand-rolled crypto |
| ``did:key`` codec | ``base58`` (PyPI) + multicodec prefix | Tiny audited helper; matches W3C spec |
| Key persistence | ``base64`` from stdlib | Simple ``base64(priv_seed)\|base64(pub)`` format |

The JWS payload shape (``@context``, ``type``, ``issuer``, ``validFrom``, ``credentialSubject``)
is **byte-identical** with the prior Kotlin ``JwsSigner.kt:39-57`` so any existing JWS consumer
(PDC, other DVAs, downstream wallets) can verify a Python-issued credential with the Kotlin
verifier and vice-versa.

## Run locally (dev)

```bash
cd data-veracity-main/dva-vc-manager
uv sync
uv run pytest                # tests (FakeWhitelist + temp signing key, no Postgres needed)
uv run dva-vc-manager         # boot the service on :8000
```

## Configuration (.env)

| Var | Default | Purpose |
|---|---|---|
| ``DVA_VC_MANAGER_SIGNING_KEY_PATH`` | ``/data/dva-vc-signing-key.pem`` | Ed25519 key file path (created 0600 on first boot) |
| ``DVA_VC_MANAGER_DB_URL`` | *(empty)* | Postgres DSN for the whitelist. Empty → in-memory ``FakeWhitelist`` (verify path fails-closed until admin populates it). |
| ``DVA_VC_MANAGER_API_KEY`` | *(empty)* | Shared-secret bearer for ``/admin/*``. When empty, admin endpoints are disabled. |
| ``DVA_VC_MANAGER_PORT`` | ``8000`` | Listen port |
| ``DVA_VC_MANAGER_LOG_LEVEL`` | ``INFO`` | Standard Python log-level name |