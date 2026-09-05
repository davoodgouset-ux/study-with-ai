# ==============================================================================
# File: app/models/user.py
# Purpose: Defines the SQLAlchemy User database model mapped to the 'users' table in MySQL.
# ==============================================================================

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from app.core.database import Base

class User(Base):
    """
    SQLAlchemy User Model.
    Each instance of this class corresponds to one row in the MySQL 'users' table.
    """
    # Table name in MySQL database
    __tablename__ = "users"

    # Primary key: unique integer ID for each user, auto-incremented by MySQL
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Full name of the user
    name = Column(String(100), nullable=False)

    # Email address: must be unique so two users cannot register with the same email
    email = Column(String(150), unique=True, index=True, nullable=False)

    # Password: store string password (in Phase 5 this will be securely hashed with bcrypt)
    password = Column(String(255), nullable=False)

    # Timestamp indicating when the account was registered
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>"
