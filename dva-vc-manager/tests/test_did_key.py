"""did:key codec round-trip tests — mirror ``DidKeyTest.kt`` exactly."""

from __future__ import annotations

from nacl.signing import SigningKey
from nacl.public import PublicKey

from dva_vc_manager.did_key import (
    did_key_to_public_key,
    public_key_to_did_key,
)


def test_ed25519_key_round_trips_through_did_key() -> None:
    signing_key = SigningKey.generate()
    pub = PublicKey(bytes(signing_key.verify_key))

    did_key = public_key_to_did_key(pub)
    round_tripped_pub = did_key_to_public_key(did_key)
    round_tripped_did_key = public_key_to_did_key(round_tripped_pub)

    assert did_key == round_tripped_did_key, (
        "did:key round-trip must produce the same identifier"
    )


def test_known_spec_vector() -> None:
    expected = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"
    pub = did_key_to_public_key(expected)
    reencoded = public_key_to_did_key(pub)
    assert reencoded == expected


def test_starts_with_did_key_z6mk() -> None:
    signing_key = SigningKey.generate()
    pub = PublicKey(bytes(signing_key.verify_key))
    did_key = public_key_to_did_key(pub)
    assert did_key.startswith("did:key:z6Mk"), (
        "did:key identifier must start with 'did:key:z6Mk'"
    )