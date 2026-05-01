"""
auth.py — JWT authentication helpers for the Mizan API.

Users are stored in an in-memory dict keyed by email.
Swap _USERS for a real DB query when you add a users table with password_hash.

Environment variables:
  JWT_SECRET   — signing secret (defaults to a dev placeholder)
  JWT_EXPIRE   — token lifetime in minutes (default: 60)
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY: str = os.getenv("JWT_SECRET", "mizan-dev-secret-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE", "60"))

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

# auto_error=False so we can return 401 instead of FastAPI's default 403
_bearer = HTTPBearer(auto_error=False)

# email → {user_id, name, email, hashed_password}
_USERS: dict[str, dict] = {}


# ── password helpers ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return _pwd.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


# ── token helpers ─────────────────────────────────────────────────────────────

def create_access_token(user_id: str, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": user_id, "email": email, "exp": expire},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


# ── user store operations ─────────────────────────────────────────────────────

def register_user(name: str, email: str, password: str) -> dict:
    """Create and store a new user. Raises ValueError if email is taken."""
    if email in _USERS:
        raise ValueError(f"Email already registered: {email}")
    user = {
        "user_id": str(uuid.uuid4()),
        "name": name,
        "email": email,
        "hashed_password": hash_password(password),
    }
    _USERS[email] = user
    return user


def login_user(email: str, password: str) -> str:
    """Return a JWT token. Raises ValueError on bad credentials."""
    user = _USERS.get(email)
    if not user or not verify_password(password, user["hashed_password"]):
        raise ValueError("Invalid email or password")
    return create_access_token(user["user_id"], email)


# ── FastAPI dependency ────────────────────────────────────────────────────────

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> dict:
    """
    FastAPI dependency. Inject with Depends(get_current_user).
    Returns the user dict on success; raises HTTP 401 otherwise.
    """
    _unauth = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated — provide a valid Bearer token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise _unauth
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("email")
        if not email or email not in _USERS:
            raise _unauth
        return _USERS[email]
    except JWTError:
        raise _unauth
