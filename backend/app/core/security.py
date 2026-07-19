"""
Authentication and Password Hashing Security Utilities.

Provides bcrypt password hashing, verification, and HS256 JWT access and refresh token generation.
"""
import os
from datetime import datetime, timedelta
from typing import Any, Optional, Union

import jwt
from passlib.context import CryptContext

# Configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "supersecretjwtkeyforfifawc2026jwtencryption123!")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a hashed password string.

    Args:
        plain_password: Candidate plain password.
        hashed_password: Stored bcrypt hash string.

    Returns:
        True if password matches hash, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Compute bcrypt hash string for a plain-text password.

    Args:
        password: Plain password string to hash.

    Returns:
        Bcrypt hashed string representation.
    """
    return pwd_context.hash(password)


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generate a signed JWT access token.

    Args:
        subject: Token subject claim (typically username).
        expires_delta: Optional custom expiration timedelta.

    Returns:
        Encoded JWT token string.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generate a signed JWT refresh token.

    Args:
        subject: Token subject claim (typically username).
        expires_delta: Optional custom expiration timedelta.

    Returns:
        Encoded JWT refresh token string.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """Decode and validate a JWT token, returning the subject claim if valid.

    Args:
        token: Signed JWT token string.
        token_type: Expected token type claim ('access' or 'refresh').

    Returns:
        Subject username string if token is valid, None otherwise.
    """
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if decoded_token.get("type") == token_type:
            return decoded_token.get("sub")
        return None
    except jwt.PyJWTError:
        return None
