# ==============================================================================
# File: app/schemas/user.py
# Purpose: Pydantic schemas for data validation and response formatting for User APIs.
# ==============================================================================

from datetime import datetime
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    """
    Schema for creating a new user (Request Body for POST /users).
    Defines what fields the client MUST provide.
    """
    name: str                           # User's full name (required)
    email: str                          # User's email address (required)
    password: str                       # User's password (required)


class UserResponse(BaseModel):
    """
    Schema for returning user information back to the client.
    SECURITY NOTICE: The 'password' field is deliberately EXCLUDED so we never leak passwords!
    """
    id: int
    name: str
    email: str
    created_at: datetime

    # ConfigDict / from_attributes = True tells Pydantic to automatically read data
    # from SQLAlchemy ORM models (e.g. user.id, user.name) instead of only dicts.
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """
    Schema for user login (Request Body for POST /auth/login).
    """
    email: str                          # Registered email address
    password: str                       # Plain-text password to verify against bcrypt hash


class Token(BaseModel):
    """
    Schema for JWT Token response.
    Returns the JWT string and token type (Bearer).
    """
    access_token: str
    token_type: str = "bearer"
    user: UserResponse                  # Profile info of the logged-in user
