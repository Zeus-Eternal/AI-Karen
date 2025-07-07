from __future__ import annotations

from cryptography.fernet import Fernet

import os


ENCRYPTION_KEY = os.getenv("KARI_JOB_ENC_KEY")
if not ENCRYPTION_KEY:
    raise RuntimeError("KARI_JOB_ENC_KEY must be set in the environment!")

_fernet = Fernet(
    ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY
)


def encrypt_data(data: bytes | str) -> bytes:
    if isinstance(data, str):
        data = data.encode()
    return _fernet.encrypt(data)


def decrypt_data(token: bytes | memoryview | None) -> str | None:
    if token is None:
        return None
    if isinstance(token, memoryview):
        token = token.tobytes()
    return _fernet.decrypt(token).decode()
