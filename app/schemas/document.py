# ==============================================================================
# File: app/schemas/document.py
# Purpose: Pydantic schemas for document upload and metadata responses.
# ==============================================================================

from datetime import datetime
from pydantic import BaseModel

class DocumentResponse(BaseModel):
    """
    Schema representing an uploaded PDF document.
    """
    id: int
    user_id: int
    filename: str
    file_size: int
    page_count: int
    uploaded_at: datetime

    class Config:
        from_attributes = True


class DocumentUploadResult(BaseModel):
    """
    Response returned when a PDF is uploaded, validated, and chunked.
    Contains document metadata, total chunks created, and sample extracted text.
    """
    status: str
    message: str
    document: DocumentResponse
    total_chunks: int
    sample_extracted_text: str


class ChunkResponse(BaseModel):
    """
    Schema representing an individual text chunk from a document.
    """
    id: int
    document_id: int
    page_number: int
    chunk_index: int
    char_count: int
    chunk_text: str

    class Config:
        from_attributes = True


class SearchResult(BaseModel):
    """
    Schema representing a retrieved chunk from FAISS similarity search.
    """
    rank: int
    score: float
    page_number: int
    chunk_index: int
    char_count: int
    chunk_text: str
