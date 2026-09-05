# ==============================================================================
# File: app/core/database.py
# Purpose: Manages the MySQL database connection using SQLAlchemy.
# Provides the engine, session factory, and a get_db dependency for FastAPI routes.
# ==============================================================================

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Step 1: Load environment variables from the .env file
load_dotenv()

# Step 2: Read the database connection URL from environment variables
# Format: mysql+pymysql://<username>:<password>@<host>:<port>/<database_name>
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:root@localhost:3306/study_with_ai"
)

# Step 3: Create the SQLAlchemy Engine
# The engine is the central object that manages connections to the MySQL server.
# 'pool_pre_ping=True' automatically tests if a connection is still alive before using it.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False  # Set to True if you want to print every raw SQL query to the terminal
)

# Step 4: Create a SessionLocal class
# Each instance of SessionLocal represents an individual database session/transaction.
# - autocommit=False: ensures we explicitly commit transactions for safety
# - autoflush=False: prevents sending premature queries before we are ready
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Step 5: Create a Base class for our database models
# All our database table classes (User, Document, etc.) will inherit from this Base.
Base = declarative_base()

# Step 6: Define the get_db Dependency for FastAPI routes
# This is a Python generator function (uses 'yield'):
# 1. Opens a new database session for an incoming HTTP request.
# 2. Hands the session to the route function to read/write data.
# 3. Always closes the session when the request finishes, preventing memory leaks!
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
