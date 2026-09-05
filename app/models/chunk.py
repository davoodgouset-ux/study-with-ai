# ==============================================================================
# File: app/models/chunk.py
# Purpose: Defines the SQLAlchemy model for storing text chunks in MySQL.
# Maps to the 'document_chunks' table with page number & document foreign key.
# ==============================================================================

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.document import Document

class DocumentChunk(Base):
    """
    SQLAlchemy DocumentChunk Model.
    Each row represents a ~1000 character passage from an uploaded PDF.
    """
    __tablename__ = "document_chunks"

    # Primary key: unique integer ID for each chunk
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Foreign key pointing to the parent document in MySQL
    # If the document is deleted, all its chunks are automatically deleted (CASCADE)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)

    # The exact page number in the PDF where this chunk came from (e.g. Page 12)
    # This powers our accurate AI citations!
    page_number = Column(Integer, nullable=False)

    # Sequential position of this chunk within the document (0, 1, 2, ...)
    chunk_index = Column(Integer, nullable=False)

    # The actual text content of the chunk (~1000 characters)
    chunk_text = Column(Text, nullable=False)

    # Total number of characters in this chunk
    char_count = Column(Integer, nullable=False)

    # Timestamp when this chunk was created
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationship back to Document model
    document = relationship("Document", backref="chunks")

    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, doc_id={self.document_id}, page={self.page_number}, idx={self.chunk_index}, chars={self.char_count})>"
