class Fernet:
    def __init__(self, key: bytes):
        self.key = key

    @staticmethod
    def generate_key() -> bytes:
        return b"testkeytestkeytestkey12345678"

    def encrypt(self, data: bytes) -> bytes:
        return b"enc" + data

    def decrypt(self, token: bytes) -> bytes:
        if token.startswith(b"enc"):
            return token[3:]
        return token
