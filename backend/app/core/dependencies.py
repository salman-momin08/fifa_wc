"""
FastAPI Dependency Injections and Authentication Helpers.

Provides get_current_user for JWT token decoding and RoleChecker for
Role-Based Access Control (RBAC) authorization.
"""
from typing import List

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import JWT_ALGORITHM, JWT_SECRET
from app.database import User, get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Decode incoming JWT bearer token and retrieve active User model instance.

    Args:
        token: OAuth2 bearer access token string.
        db: Database session dependency.

    Returns:
        Authenticated User instance.

    Raises:
        HTTPException: 401 if token is invalid/expired, or 400 if user is inactive.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        if username is None or token_type != "access":
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return user


class RoleChecker:
    """RBAC dependency class enforcing allowed role permissions on endpoints."""

    def __init__(self, allowed_roles: List[str]) -> None:
        """Initialize with a list of permitted role name strings.

        Args:
            allowed_roles: List of allowed role names (e.g. ['organizer', 'admin']).
        """
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_user)) -> User:
        """Verify authenticated user role matches at least one allowed role.

        Args:
            current_user: Authenticated User model instance.

        Returns:
            User model instance if authorized.

        Raises:
            HTTPException: 403 Forbidden if user role is not permitted.
        """
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have the required permissions to access this resource",
            )
        return current_user
