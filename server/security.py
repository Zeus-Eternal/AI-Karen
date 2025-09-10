# mypy: ignore-errors
"""
Security configuration for Kari FastAPI Server.
Handles password context, API key headers, OAuth2 schemes, and SSL context.
"""

import ssl
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from passlib.context import CryptContext

# Security Setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)


def get_ssl_context():
    """Create and configure SSL context for secure connections"""
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
    ssl_context.set_ciphers("ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384")
    ssl_context.load_cert_chain("cert.pem", "key.pem")
    return ssl_context