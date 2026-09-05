# ==============================================================================
# File: app/services/rag_service.py
# Purpose: Full RAG Pipeline Orchestrator.
# Enforces Multi-Tenant Isolation, FAISS Retrieval, Lost-in-the-Middle Reordering,
# and Citation Parsing.
# ==============================================================================

import os
import re
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Document, DocumentChunk
from app.services.embedding_service import EmbeddingUnavailableError
from app.services.vector_service import search_document_chunks
from app.services.prompt_templates import build_rag_qa_prompt
from app.services.gemini_service import generate_rag_answer

# Tune this with the project's evaluation dataset: score distributions vary by
# embedding model and subject matter.
MIN_RETRIEVAL_SCORE = float(os.getenv("MIN_RETRIEVAL_SCORE", "0.35"))


def _no_answer_response(top_similarity_score: float = 0.0) -> dict:
    return {
        "answer": "The requested information cannot be found in the uploaded document.",
        "citations": [],
        "retrieved_chunks": [],
        "top_similarity_score": top_similarity_score,
        "model_used": "retrieval-guardrail",
    }


def answer_question_about_document(
    user_id: int,
    document_id: int,
    question: str,
    db: Session,
    top_k: int = 5
) -> dict:
    """
    Executes end-to-end RAG question-answering over an uploaded document.
    
    Security & Guardrail Checks:
    1. Multi-Tenant Check: Verifies document is owned by current user.
    2. FAISS Semantic Search: Retrieves Top-K chunks.
    3. Reordering: Combats 'lost-in-the-middle' attention bias.
    4. Anti-Hallucination: Grounded strictly in textbook context.
    """
    # Step 1: Security Layer 1 - Verify document ownership
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == user_id
    ).first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} was not found or access is denied."
        )

    # Step 2: Retrieve Top-K most relevant chunks using FAISS
    try:
        chunks = search_document_chunks(
            user_id=user_id,
            document_id=document_id,
            query=question,
            db=db,
            top_k=top_k
        )
    except EmbeddingUnavailableError as exc:
        # Never generate an answer from random or incompatible vectors.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Semantic search is temporarily unavailable. Please try again shortly."
        ) from exc

    # Step 3: Security Layer 2 - Similarity threshold guardrail
    if not chunks:
        return _no_answer_response()

    # FAISS always has a nearest neighbour when chunks exist. A low score means
    # that nearest passage is still not relevant and must not reach the LLM.
    if chunks[0]["score"] < MIN_RETRIEVAL_SCORE:
        return _no_answer_response(chunks[0]["score"])

    # Step 4: Reorder chunks to combat LLM 'Lost-in-the-Middle' effect
    # (Puts Rank 1 at the top, Rank 2 at the bottom, and others in between)
    reordered_chunks = reorder_chunks_for_attention(chunks)

    # Step 5: Build secure XML-delimited prompt
    prompt = build_rag_qa_prompt(
        document_filename=doc.filename,
        context_chunks=reordered_chunks,
        student_question=question
    )

    # Step 6: Generate cited answer using Gemini
    raw_answer, model_name = generate_rag_answer(prompt)

    # Step 7: Extract all page citations present in the answer (e.g. Page 1, Page 2)
    cited_pages = extract_citations_from_text(raw_answer)
    allowed_page_numbers = {chunk["page_number"] for chunk in chunks}
    cited_pages = [
        citation for citation in cited_pages
        if any(f"Page {page_number}" in citation for page_number in allowed_page_numbers)
    ]

    # If the model didn't write citations explicitly, supply the primary source page
    if not cited_pages and chunks:
        primary_page = chunks[0]["page_number"]
        cited_pages = [f"{doc.filename} — Page {primary_page}"]

    return {
        "answer": raw_answer,
        "citations": cited_pages,
        "retrieved_chunks": [
            {
                "rank": c["rank"],
                "score": c["score"],
                "page_number": c["page_number"],
                "snippet": c["chunk_text"][:150] + "..."
            }
            for c in chunks
        ],
        "top_similarity_score": chunks[0]["score"] if chunks else 0.0,
        "model_used": model_name
    }


def reorder_chunks_for_attention(chunks: list[dict]) -> list[dict]:
    """
    Reorders chunks so the most relevant chunk is at the beginning and the 2nd
    most relevant is at the end, maximizing LLM attention recall.
    """
    if len(chunks) <= 2:
        return chunks

    reordered = []
    # Rank 1 at top
    reordered.append(chunks[0])

    # Middle chunks (Ranks 3, 4, 5...)
    if len(chunks) > 2:
        reordered.extend(chunks[2:])

    # Rank 2 at bottom
    reordered.append(chunks[1])
    return reordered


def extract_citations_from_text(text: str) -> list[str]:
    """
    Finds and extracts page citations matching '[... Page X]' or 'Page X' from answer text.
    """
    matches = re.findall(r'\[([^\]]*?Page\s+\d+[^\]]*?)\]', text)
    return list(dict.fromkeys(matches))
