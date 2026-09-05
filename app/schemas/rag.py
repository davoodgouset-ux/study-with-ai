# ==============================================================================
# File: app/schemas/rag.py
# Purpose: Pydantic schemas for RAG Q&A requests and cited responses.
# ==============================================================================

from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    """
    Request payload for asking a question about an uploaded document.
    """
    question: str = Field(..., min_length=2, max_length=1000, description="The study question to ask")
    top_k: int = Field(5, ge=1, le=10, description="Number of context chunks to retrieve from FAISS")


class RetrievedChunkInfo(BaseModel):
    """
    Metadata of a chunk retrieved by FAISS for citation and transparency.
    """
    rank: int
    score: float
    page_number: int
    snippet: str


class QuestionResponse(BaseModel):
    """
    Response schema returning the AI answer, exact page citations, and retrieved passages.
    """
    answer: str
    citations: list[str]
    retrieved_chunks: list[RetrievedChunkInfo]
    top_similarity_score: float
    model_used: str
