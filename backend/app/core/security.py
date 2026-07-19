"""
Authentication and Password Hashing Security Utilities.

Provides bcrypt password hashing, verification, and HS256 JWT access and refresh token generation.
"""
from datetime import datetime, timedelta, timezone
import os
from typing import Any, Optional, Union

import bcrypt
import jwt

# Configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "supersecretjwtkeyforfifawc2026jwtencryption123!")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain-text password against a hashed bcrypt digest.

    Args:
        plain_password: User-provided input password.
        hashed_password: Stored bcrypt hashed string.

    Returns:
        True if password matches hash, False otherwise.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Compute bcrypt hash string for a plain-text password.

    Args:
        password: Plain password string to hash.

    Returns:
        Bcrypt hashed string representation.
    """
    pwd_bytes = (password or "").encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generate a signed JWT access token.

    Args:
        subject: Token subject claim (typically username).
        expires_delta: Optional custom expiration timedelta.

    Returns:
        Encoded JWT token string.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generate a long-lived signed JWT refresh token.

    Args:
        subject: Token subject claim.
        expires_delta: Optional custom expiration timedelta.

    Returns:
        Encoded JWT token string.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """Verify and decode a JWT token string, returning the subject (username).

    Args:
        token: JWT string to verify.
        token_type: Expected token type ("access" or "refresh").

    Returns:
        Subject username string if valid, None otherwise.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: Optional[str] = payload.get("sub")
        payload_type: Optional[str] = payload.get("type")
        if username is None or payload_type != token_type:
            return None
        return username
    except jwt.PyJWTError:
        return None
