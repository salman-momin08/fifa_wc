"""
OAuth2 Authentication and User Registration Router.

Provides JWT token issuance, refresh token rotation, user registration,
and authenticated profile (/me) endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.security import create_access_token, create_refresh_token, get_password_hash, verify_password, verify_token
from app.database import User, get_db
from app.schemas.auth import Token, UserOut, UserRegister

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(user_in: UserRegister, db: Session = Depends(get_db)) -> User:
    """Register a new user account with hashed password credentials.

    Args:
        user_in: User registration schema payload.
        db: Database session dependency.

    Returns:
        Created User record instance.

    Raises:
        HTTPException: 400 if username is already registered.
    """
    existing_user = db.query(User).filter(User.username == user_in.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    hashed_pwd = get_password_hash(user_in.password)
    new_user = User(
        username=user_in.username,
        hashed_password=hashed_pwd,
        role=user_in.role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
) -> dict:
    """Authenticate username and password credentials to issue JWT access and refresh tokens.

    Args:
        form_data: OAuth2 password form containing username and password.
        db: Database session dependency.

    Returns:
        Dictionary containing access_token, refresh_token, and bearer token_type.

    Raises:
        HTTPException: 401 if credentials are invalid or user is inactive.
    """
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token = create_access_token(subject=user.username)
    refresh_token = create_refresh_token(subject=user.username)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
def refresh_access_token(refresh_token: str, db: Session = Depends(get_db)) -> dict:
    """Issue a new access token using a valid refresh token.

    Args:
        refresh_token: Signed refresh JWT string.
        db: Database session dependency.

    Returns:
        Dictionary with fresh access_token and refresh_token.

    Raises:
        HTTPException: 401 if refresh token is invalid or expired.
    """
    username = verify_token(refresh_token, token_type="refresh")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=400, detail="User not active")

    access_token = create_access_token(subject=user.username)
    new_refresh_token = create_refresh_token(subject=user.username)

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserOut)
def read_users_me(current_user: User = Depends(get_current_user)) -> User:
    """Retrieve profile information for the currently authenticated user.

    Args:
        current_user: User model injected by JWT dependency.

    Returns:
        User model instance.
    """
    return current_user
