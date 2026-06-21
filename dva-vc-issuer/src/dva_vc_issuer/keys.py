import os
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

from .config import DVA_VC_KEY_PATH, DVA_VC_KEY_ID


def load_or_create_key_pair() -> rsa.RSAPrivateKey:
    key_path = Path(DVA_VC_KEY_PATH)
    key_dir = key_path.parent
    key_dir.mkdir(parents=True, exist_ok=True)

    if key_path.exists():
        with open(key_path, "rb") as f:
            private_key = serialization.load_pem_private_key(
                f.read(), password=None, backend=default_backend()
            )
        return private_key

    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )

    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    with open(key_path, "wb") as f:
        f.write(pem)
        os.chmod(key_path, 0o600)

    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    public_path = key_path.with_suffix(".pub.pem")
    with open(public_path, "wb") as f:
        f.write(public_pem)

    return private_key


def get_public_key_jwk(private_key: rsa.RSAPrivateKey) -> dict:
    public_key = private_key.public_key()
    numbers = public_key.public_numbers()

    def _int_to_base64url(n: int) -> str:
        import base64
        byte_length = (n.bit_length() + 7) // 8
        b = n.to_bytes(byte_length, "big")
        return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")

    return {
        "kty": "RSA",
        "n": _int_to_base64url(numbers.n),
        "e": _int_to_base64url(numbers.e),
        "alg": "PS256",
        "kid": DVA_VC_KEY_ID,
        "use": "sig",
    }