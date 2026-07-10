"""Signing key store tests — mirror ``SigningKeyStoreTest.kt``."""

from __future__ import annotations

import os
from pathlib import Path

from dva_vc_manager.did_key import public_key_to_did_key
from dva_vc_manager.keys import SigningKeyStore
from nacl.public import PublicKey


def test_generates_key_on_first_run_when_file_missing(tmp_path: Path) -> None:
    key_path = tmp_path / "subdir" / "key.pem"
    store = SigningKeyStore(str(key_path))

    pair = store.load_or_generate()

    assert key_path.exists(), "Key file must be created on first run"
    assert pair.private is not None
    assert pair.public is not None
    # Permissions: 0600 on POSIX
    if os.name == "posix":
        assert (key_path.stat().st_mode & 0o777) == 0o600


def test_persists_and_reloads_the_same_key_across_instances(tmp_path: Path) -> None:
    key_path = tmp_path / "key.pem"

    store1 = SigningKeyStore(str(key_path))
    pair1 = store1.load_or_generate()
    pub1_bytes = bytes(pair1.public)

    # New instance pointing at the same file — must load, not regenerate.
    store2 = SigningKeyStore(str(key_path))
    pair2 = store2.load_or_generate()
    pub2_bytes = bytes(pair2.public)

    assert pub1_bytes == pub2_bytes, (
        "reload must yield the same public key as the original generation"
    )


def test_derived_did_key_starts_with_z6mk(tmp_path: Path) -> None:
    store = SigningKeyStore(str(tmp_path / "key.pem"))
    store.load_or_generate()
    did_key = store.issuer_did_key()
    assert did_key.startswith("did:key:z6Mk")