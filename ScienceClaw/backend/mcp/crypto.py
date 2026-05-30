import base64
import hashlib
import hmac
import secrets
from typing import Final


_VERSION: Final[str] = "v1"
_DIGEST_SIZE: Final[int] = 32
_NONCE_SIZE: Final[int] = 16
_MASK_VISIBLE_CHARS: Final[int] = 4


def encrypt_secret(secret: str | None, key: str | bytes | None) -> str:
    if not secret:
        return ""
    key_bytes = _normalize_key(key)
    nonce = secrets.token_bytes(_NONCE_SIZE)
    secret_bytes = secret.encode("utf-8")
    keystream = _derive_stream(key_bytes, nonce, len(secret_bytes))
    ciphertext = _xor_bytes(secret_bytes, keystream)
    signature = hmac.new(key_bytes, nonce + ciphertext, hashlib.sha256).digest()
    payload = nonce + ciphertext + signature
    return f"{_VERSION}:{base64.urlsafe_b64encode(payload).decode('ascii')}"


def decrypt_secret(encrypted: str | None, key: str | bytes | None) -> str:
    if not encrypted:
        return ""
    key_bytes = _normalize_key(key)
    payload = _decode_payload(encrypted)
    if len(payload) <= _NONCE_SIZE + _DIGEST_SIZE:
        raise ValueError("Invalid encrypted secret payload")
    nonce = payload[:_NONCE_SIZE]
    signature = payload[-_DIGEST_SIZE:]
    ciphertext = payload[_NONCE_SIZE:-_DIGEST_SIZE]
    expected = hmac.new(key_bytes, nonce + ciphertext, hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected):
        raise ValueError("Invalid encrypted secret signature")
    keystream = _derive_stream(key_bytes, nonce, len(ciphertext))
    return _xor_bytes(ciphertext, keystream).decode("utf-8")


def mask_secret(secret: str | None) -> str:
    if not secret:
        return ""
    if len(secret) <= _MASK_VISIBLE_CHARS:
        return "*" * len(secret)
    return f"{'*' * 8}{secret[-_MASK_VISIBLE_CHARS:]}"


def _normalize_key(key: str | bytes | None) -> bytes:
    if key is None:
        raise ValueError("Encryption key is required")
    key_bytes = key.encode("utf-8") if isinstance(key, str) else key
    if not key_bytes:
        raise ValueError("Encryption key is required")
    return hashlib.sha256(key_bytes).digest()


def _decode_payload(encrypted: str) -> bytes:
    prefix = f"{_VERSION}:"
    if not encrypted.startswith(prefix):
        raise ValueError("Unsupported encrypted secret format")
    encoded = encrypted[len(prefix):]
    try:
        padding = "=" * (-len(encoded) % 4)
        return base64.b64decode(
            (encoded + padding).encode("ascii"),
            altchars=b"-_",
            validate=True,
        )
    except Exception as exc:
        raise ValueError("Invalid encrypted secret payload") from exc


def _derive_stream(key: bytes, nonce: bytes, size: int) -> bytes:
    blocks = []
    counter = 0
    generated = 0
    while generated < size:
        counter_bytes = counter.to_bytes(4, "big")
        block = hmac.new(key, nonce + counter_bytes, hashlib.sha256).digest()
        blocks.append(block)
        generated += len(block)
        counter += 1
    return b"".join(blocks)[:size]


def _xor_bytes(left: bytes, right: bytes) -> bytes:
    return bytes(a ^ b for a, b in zip(left, right))
