# ==============================================================================
# File: app/core/security.py
# Purpose: Security utilities for password hashing (bcrypt) and JWT token generation.
# ==============================================================================

import os
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from .env with secure defaults
SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "study_with_ai_super_secret_jwt_key_2026_cse_final_year_project_secure"
)
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours


# ==============================================================================
# 1. Password Hashing with bcrypt
# ==============================================================================

def hash_password(password: str) -> str:
    """
    Hashes a plain-text password using the bcrypt algorithm.
    
    How it works:
    1. Generates a random cryptographic 'salt' (unique per user).
    2. Combines salt + password and runs multiple rounds of mathematical hashing.
    3. Returns an irreversible string (e.g., '...').
    """
    # bcrypt requires bytes, so we encode the string to UTF-8
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies if a plain-text password matches the stored bcrypt hash.
    
    How it works:
    Extracts the salt from the stored hash, hashes the plain password with that salt,
    and checks if the resulting hashes match. Returns True if correct, False otherwise.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


# ==============================================================================
# 2. JWT (JSON Web Token) Generation & Verification
# ==============================================================================

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Creates a digitally signed JWT access token.
    
    A JWT has 3 parts separated by dots (header.payload.signature):
    1. Header: Specifies the algorithm (HS256).
    2. Payload: User identity ('sub': user_email) and expiration timestamp ('exp').
    3. Signature: Cryptographic hash proving the token was created by our server.
    """
    to_encode = data.copy()
    
    # Set expiration time (default: 24 hours from now)
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    
    # Digitally sign the token using our SECRET_KEY
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict | None:
    """
    Decodes and validates a JWT token.
    Checks signature integrity and expiration time.
    Returns the decoded payload dict if valid, or None if invalid/expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
