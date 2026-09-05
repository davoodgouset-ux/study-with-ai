# ==============================================================================
# File: app/api/auth.py
# Purpose: Authentication routes for Registration, Login (JWT), and Protected Profile.
# ==============================================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserLogin, Token

# Create a dedicated APIRouter for authentication
router = APIRouter(prefix="/auth", tags=["Authentication"])


# ==============================================================================
# 1. User Registration with Password Hashing
# ==============================================================================
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Registers a new student/user account.
    
    Security: The password is NEVER saved as plain text. It is hashed using
    bcrypt with salt before saving to MySQL.
    """
    # Step 1: Prevent duplicate email registration
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration failed: Email '{user_data.email}' is already in use."
        )

    # Step 2: Hash the password securely using bcrypt
    hashed_pwd = hash_password(user_data.password)

    # Step 3: Create the User database record with the HASHED password
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password=hashed_pwd  # Stored as irreversible hash (e.g., $...)
    )

    # Step 4: Save to MySQL database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# ==============================================================================
# 2. User Login & JWT Token Generation
# ==============================================================================
@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticates user credentials and issues a secure JWT Bearer Token.
    """
    # Step 1: Find the user in MySQL by email
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user:
        # Security best practice: do not reveal whether the email exists
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Step 2: Verify the plain password against the stored bcrypt hash
    if not verify_password(login_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Step 3: Generate a signed JWT token containing user identity ('sub')
    access_token = create_access_token(data={"sub": user.email, "id": user.id})

    # Step 4: Return the token and user profile
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


# ==============================================================================
# 3. Protected Endpoint: Current Logged-in User Profile
# ==============================================================================
@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """
    Protected Endpoint.
    Only accessible if the client sends a valid 'Authorization: Bearer <token>' header.
    Returns the authenticated student's profile.
    """
    return current_user
