# ==============================================================================
# File: app/core/dependencies.py
# Purpose: FastAPI dependencies for authentication and route protection.
# ==============================================================================

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

# HTTPBearer tells FastAPI and Swagger UI:
# In the Authorize popup (🔒), show a single clean input box: 'Value: [paste your JWT token here]'
# No confusing username/password/client_id fields!
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency that extracts, verifies the JWT token, and retrieves the logged-in user.
    
    Any route that includes 'current_user: User = Depends(get_current_user)'
    is automatically PROTECTED. If the token is invalid or missing,
    FastAPI immediately returns a 401 Unauthorized error.
    """
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or token expired",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Step 1: Decode and verify JWT signature and expiration
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
        
    # Step 2: Extract user email from the 'sub' (subject) claim
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
        
    # Step 3: Query MySQL to ensure the user still exists in the database
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
        
    # Return the authenticated user model
    return user
