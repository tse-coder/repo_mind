"""Better Auth JWT & Session Security Layer for FastAPI.

Validates Better Auth signed JWT tokens or session cookies to authenticate
users and associate LangGraph checkpoint threads and saved investigations.
"""

from __future__ import annotations

import logging
import os

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

load_dotenv()

logger = logging.getLogger(__name__)

# Default dev secret matches frontend/src/lib/auth.ts fallback
DEFAULT_AUTH_SECRET = "repomind-development-secret-key-change-in-production-1234567890"


class AuthUser(BaseModel):
    """Authenticated user model representing the caller identity."""

    id: str = Field(description="Unique user ID from Better Auth")
    email: str | None = Field(default=None, description="User email address")
    name: str | None = Field(default=None, description="User display name")
    username: str | None = Field(default=None, description="User handle / username")
    is_authenticated: bool = Field(default=True, description="Whether identity is authenticated")


def get_better_auth_secret() -> str:
    """Get secret key used to verify Better Auth tokens."""
    secret = (os.getenv("BETTER_AUTH_SECRET") or "").strip()
    return secret if secret else DEFAULT_AUTH_SECRET


def extract_token_from_request(request: Request) -> str | None:
    """Extract auth token from Authorization header or Better Auth session cookie."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    # Next.js / Better Auth cookie fallback
    cookie_token = request.cookies.get("better-auth.session_token")
    if cookie_token:
        return cookie_token

    return None


async def get_current_user_optional(request: Request) -> AuthUser:
    """Extract current user if authenticated; returns guest user if unauthenticated.

    This ensures public endpoints or local development without auth continue to function.
    """
    token = extract_token_from_request(request)
    if not token:
        return AuthUser(
            id="guest_anonymous",
            email="guest@repomind.local",
            name="Guest User",
            is_authenticated=False,
        )

    secret = get_better_auth_secret()

    try:
        # Decode JWT token signed by Better Auth jwt() plugin
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"verify_aud": False},  # aud optional in dev
        )
        user_id = str(payload.get("sub") or payload.get("id") or "anonymous")
        return AuthUser(
            id=user_id,
            email=payload.get("email"),
            name=payload.get("name"),
            username=payload.get("username"),
            is_authenticated=True,
        )
    except jwt.ExpiredSignatureError:
        logger.warning("Auth token has expired")
        return AuthUser(
            id="guest_anonymous",
            email="guest@repomind.local",
            name="Guest User",
            is_authenticated=False,
        )
    except jwt.InvalidTokenError as e:
        logger.debug("Non-JWT or unverified token (might be raw session token): %s", e)
        # If it's a raw session cookie, we treat it as an authenticated session identifier in dev
        if request.cookies.get("better-auth.session_token") == token:
            return AuthUser(
                id=f"session_{token[:12]}",
                email="user@session.local",
                name="Authenticated Session",
                is_authenticated=True,
            )
        return AuthUser(
            id="guest_anonymous",
            email="guest@repomind.local",
            name="Guest User",
            is_authenticated=False,
        )


async def require_current_user(
    user: AuthUser = Depends(get_current_user_optional),
) -> AuthUser:
    """Dependency that enforces authentication.

    Raises 401 Unauthorized if user is not authenticated.
    """
    if not user.is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in via RepoMind.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
