# dva-vc-issuer

W3C Verifiable Credential issuer with JWS (JsonWebSignature2020) signing for the Data Veracity Assurance platform.

Replaces the ACA-Py / Hyperledger Indy based `dva-acapy-controller` with a lightweight, standards-compliant implementation that does not require a distributed ledger.

## Key Management

On startup, the issuer loads or generates an RSA-2048 key pair. The private key is stored at `DVA_VC_KEY_PATH` (default: `/data/keys/private_key.pem`). The corresponding public key is embedded in the VC proof as a `did:web` verification method.

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/generate_aov` | POST | Issue a W3C VC with AoV payload, signed with JWS |
| `/verify` | POST | Verify a JWS-signed VC |
| `/.well-known/did.json` | GET | DID document for `did:web` resolution |
| `/health` | GET | Health check |