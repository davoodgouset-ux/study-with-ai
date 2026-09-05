# ==============================================================================
# File: app/models/document.py
# Purpose: Defines the SQLAlchemy Document database model mapped to the 'documents' table in MySQL.
# ==============================================================================

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Document(Base):
    """
    SQLAlchemy Document Model.
    Each record tracks one PDF file uploaded by an authenticated user.
    """
    __tablename__ = "documents"

    # Primary key: unique integer ID for each document
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign key linking the document to its owner (user)
    # This guarantees Constraint #1: User data isolation!
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    # Original filename of the uploaded PDF (e.g. 'Operating_Systems.pdf')
    filename = Column(String(255), nullable=False)

    # Safe filesystem storage path where the PDF is saved on disk (under uploads/)
    file_path = Column(String(500), nullable=False)

    # File size in bytes (Constraint: max 10MB = 10,485,760 bytes)
    file_size = Column(Integer, nullable=False)

    # Total page count extracted by PyMuPDF (Constraint: max ~100 pages)
    page_count = Column(Integer, nullable=False)

    # Timestamp when the PDF was uploaded
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationship back to User model
    owner = relationship("User", backref="documents")

    def __repr__(self):
        return f"<Document(id={self.id}, user_id={self.user_id}, filename='{self.filename}', pages={self.page_count})>"
