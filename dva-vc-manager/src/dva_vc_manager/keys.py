"""Ed25519 signing-key store.

Mirrors the Kotlin ``SigningKeyStore.kt:34`` semantics **without**
implementing any custom cryptography — keys are generated and loaded via
PyNaCl's :class:`nacl.signing.SigningKey`, which is the canonical
libsodium binding (audited, used widely in production).

Persistence format: ``base64(private key seed)|base64(public key)`` —
PyNaCl exposes the private key as a 32-byte seed, the public key as 32
bytes. The seed is the canonical "private key" representation for
Ed25519 in libsodium.

POSIX file permissions 0600 are applied to the key file, mirroring
``SigningKeyStore.kt:107-114``. Parent directories are 0700.
"""

from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Tuple

from nacl.signing import SigningKey, VerifyKey
from nacl.public import PublicKey


__all__ = ["SigningKeyStore", "KeyPair"]


class KeyPair:
    """A loaded Ed25519 keypair (PyNaCl types)."""

    def __init__(self, private: SigningKey, public: VerifyKey) -> None:
        self._private = private
        self._public = public

    @property
    def private(self) -> SigningKey:
        return self._private

    @property
    def public(self) -> VerifyKey:
        return self._public

    def public_key(self) -> PublicKey:
        """Return the PyNaCl PublicKey (needed by did_key codec)."""
        return PublicKey(bytes(self._public))


class SigningKeyStore:
    """Persistent Ed25519 keypair store backed by a filesystem path."""

    def __init__(self, path: str) -> None:
        self._path = Path(path)
        self._cached: KeyPair | None = None

    def load_or_generate(self) -> KeyPair:
        """Return the cached keypair, load from disk, or generate+persist."""
        if self._cached is not None:
            return self._cached

        if self._path.exists():
            content = self._path.read_text()
            parts = content.split("|")
            if len(parts) != 2:
                raise RuntimeError(
                    f"Signing key file at {self._path} is malformed (expected "
                    f"'base64(priv)|base64(pub)', got {len(parts)} segment(s)). "
                    "Remove the file manually if you intend to generate a new key."
                )
            priv_seed = base64.b64decode(parts[0])
            pub_bytes = base64.b64decode(parts[1])
            signing_key = SigningKey(priv_seed)
            if bytes(signing_key.verify_key) != pub_bytes:
                raise RuntimeError(
                    f"Signing key file at {self._path} is inconsistent: "
                    "public key does not match private seed. Refusing to load."
                )
            self._cached = KeyPair(signing_key, signing_key.verify_key)
            return self._cached

        # File doesn't exist — generate a fresh keypair and persist it.
        signing_key = SigningKey.generate()
        self._cached = KeyPair(signing_key, signing_key.verify_key)

        parent = self._path.parent or Path(".")
        parent.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(parent, 0o700)
        except (NotImplementedError, OSError):
            pass  # Non-POSIX filesystems (Windows)

        priv_b64 = base64.b64encode(bytes(signing_key)).decode("ascii")
        pub_b64 = base64.b64encode(bytes(signing_key.verify_key)).decode("ascii")
        self._path.write_text(f"{priv_b64}|{pub_b64}")

        try:
            os.chmod(self._path, 0o600)
        except (NotImplementedError, OSError):
            pass
        return self._cached

    def issuer_did_key(self) -> str:
        """Return the ``did:key`` identifier of the loaded public key."""
        from .did_key import public_key_to_did_key

        if self._cached is None:
            raise RuntimeError("SigningKeyStore.load_or_generate() must be called before issuer_did_key()")
        return public_key_to_did_key(self._cached.public_key())