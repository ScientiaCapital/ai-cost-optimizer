"""Authentication middleware and dependencies for Supabase JWT validation."""
import os
import logging
from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt import PyJWTError

logger = logging.getLogger(__name__)

# Supabase JWT secret from environment
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

# HTTP Bearer token scheme
security = HTTPBearer()


def verify_jwt_token(token: str) -> dict:
    """
    Verify and decode Supabase JWT token.

    Args:
        token: JWT token string from Authorization header

    Returns:
        Decoded token payload with user_id, email, role, etc.

    Raises:
        HTTPException: If token is invalid or expired
    """
    if not SUPABASE_JWT_SECRET:
        logger.error("SUPABASE_JWT_SECRET not set in environment!")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server authentication configuration error"
        )

    try:
        # Decode JWT using Supabase secret
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"  # Supabase sets aud to "authenticated"
        )

        logger.debug(f"JWT verified for user: {payload.get('sub')}")

        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except jwt.InvalidAudienceError:
        logger.warning("JWT audience mismatch")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token audience",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except PyJWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    FastAPI dependency to get current authenticated user from JWT.

    Validates the JWT token and returns the payload.

    Usage:
        @app.get("/protected")
        async def protected_endpoint(user: dict = Depends(get_current_user)):
            user_id = user["sub"]  # Supabase user ID
            email = user["email"]
            return {"message": f"Hello {email}"}

    Args:
        credentials: HTTP Bearer credentials (auto-injected by FastAPI)

    Returns:
        Decoded JWT payload with user info

    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    return verify_jwt_token(token)


def get_current_user_id(user: dict = Depends(get_current_user)) -> str:
    """
    FastAPI dependency to extract just the user_id from JWT.

    This is the most commonly used dependency for RLS-protected operations.

    Usage:
        @app.get("/my-data")
        async def get_my_data(user_id: str = Depends(get_current_user_id)):
            # user_id automatically extracted and validated
            data = await tracker.get_usage_stats()  # RLS filters by user_id
            return data

    Args:
        user: Decoded JWT payload (auto-injected by get_current_user)

    Returns:
        User ID (UUID string)
    """
    return user["sub"]  # Supabase stores user ID in "sub" claim


class OptionalAuth:
    """
    Optional authentication dependency.

    Returns user_id if authenticated, None if not.
    Useful for endpoints that work in both authenticated and public modes.

    Usage:
        @app.get("/chat")
        async def chat(user_id: Optional[str] = Depends(OptionalAuth())):
            if user_id:
                # Authenticated: Use RLS filtering
                tracker = AsyncCostTracker(user_id=user_id)
            else:
                # Public: Admin mode (no RLS)
                tracker = AsyncCostTracker(user_id=None)
    """

    def __call__(self, request: Request) -> Optional[str]:
        """Extract user_id from Authorization header if present."""
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            # No auth provided - public access
            return None

        try:
            token = auth_header.replace("Bearer ", "")
            payload = verify_jwt_token(token)
            return payload["sub"]

        except HTTPException:
            # Invalid token - public access (don't raise, just return None)
            logger.debug("Optional auth: invalid token, falling back to public access")
            return None


# Export commonly used dependencies
__all__ = [
    "get_current_user",
    "get_current_user_id",
    "OptionalAuth",
    "verify_jwt_token",
]
