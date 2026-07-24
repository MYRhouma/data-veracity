"""``did:key`` codec for Ed25519 keys.

Mirrors the Kotlin implementation in ``dva-api/api/.../jws/DidKey.kt``:

* The Ed25519 public key is encoded as 32 raw bytes (RFC 8032).
* Prefixed with the Ed25519 multicodec prefix ``0xed 0x01``.
* Then ``multibase(base58btc(...))`` — prefixed with the ``z`` character
  for base58btc.
* Finally wrapped in ``did:key:``.

This is exactly the W3C did:key specification — no custom cryptography.
``base58`` is a tiny, audited Python package; ``nacl`` is the canonical
libsodium binding (PyNaCl).

Reference:
- https://w3c-ccg.github.io/did-method-key/
- The known test vector ``did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK``
"""

from __future__ import annotations

import base58
from nacl.public import PublicKey

ED25519_RAW_SIZE = 32
ED25519_MULTICODEC_PREFIX = b"\xed\x01"
MULTIBASE_BASE58BTC_PREFIX = "z"
DID_KEY_SCHEME = "did:key:"


def public_key_to_did_key(public_key: PublicKey) -> str:
    """Encode a PyNaCl Ed25519 PublicKey into a ``did:key`` identifier."""
    raw = bytes(public_key)
    if len(raw) != ED25519_RAW_SIZE:
        raise ValueError(f"Ed25519 public key must be exactly 32 bytes, got {len(raw)}")
    multicodec = ED25519_MULTICODEC_PREFIX + raw
    return DID_KEY_SCHEME + MULTIBASE_BASE58BTC_PREFIX + base58.b58encode(multicodec).decode("ascii")


def did_key_to_public_key(did_key: str) -> PublicKey:
    """Decode a ``did:key`` Ed25519 identifier back into a PyNaCl PublicKey."""
    if not did_key.startswith(DID_KEY_SCHEME):
        raise ValueError(f"not a did:key identifier: {did_key}")
    multibase = did_key.removeprefix(DID_KEY_SCHEME)
    if not multibase.startswith(MULTIBASE_BASE58BTC_PREFIX):
        raise ValueError(f"only base58btc multibase ('z') is supported, got: {multibase}")
    decoded = base58.b58decode(multibase[1:])
    if len(decoded) != len(ED25519_MULTICODEC_PREFIX) + ED25519_RAW_SIZE:
        raise ValueError(
            f"decoded multicodec is {len(decoded)} bytes, "
            f"expected {len(ED25519_MULTICODEC_PREFIX) + ED25519_RAW_SIZE}"
        )
    if decoded[:2] != ED25519_MULTICODEC_PREFIX:
        raise ValueError(
            f"multicodec prefix 0x{decoded[0]:02x}{decoded[1]:02x} "
            "is not the Ed25519 prefix 0xed01"
        )
    return PublicKey(decoded[2:])