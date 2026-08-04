from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt

from app.config import settings
from app.schemas.auth import TokenData
from app.utils.logging import logger


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generates a signed JWT access token.

    Args:
        data: Custom claims dictionary to include in token payload.
        expires_delta: Optional custom expiration duration.

    Returns:
        str: Encoded JWT string.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire, "iat": now})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """Decodes and validates a signed JWT access token.

    Args:
        token: Encoded JWT string.

    Returns:
        Optional[TokenData]: Decoded payload if valid, None if invalid/expired.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        email: Optional[str] = payload.get("sub")
        team_id: Optional[int] = payload.get("team_id")
        is_admin: bool = payload.get("is_admin", False)

        if email is None or team_id is None:
            return None

        return TokenData(email=email, team_id=team_id, is_admin=is_admin)
    except jwt.PyJWTError as e:
        logger.warning(f"Failed to decode JWT token: {e}")
        return None
