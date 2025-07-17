import base64

class Fernet:
    def __init__(self, key: bytes) -> None:
        self.key = key

    @staticmethod
    def generate_key() -> bytes:
        return base64.urlsafe_b64encode(b'0' * 32)

    def encrypt(self, data: bytes | str) -> bytes:
        if isinstance(data, str):
            data = data.encode()
        return b'encrypted:' + data

    def decrypt(self, token: bytes) -> bytes:
        if token.startswith(b'encrypted:'):
            return token[len(b'encrypted:'):]
        return token
