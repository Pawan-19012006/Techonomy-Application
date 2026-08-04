from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict


class LoginRequest(BaseModel):
    """Payload schema for user authentication."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response schema containing JWT access token."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Internal decoded token payload schema."""

    email: Optional[str] = None
    team_id: Optional[int] = None
    is_admin: bool = False
