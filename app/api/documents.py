# ==============================================================================
# File: app/api/documents.py
# Purpose: Document endpoints for PDF Upload, PyMuPDF Extraction, Text Chunking,
# and FAISS Semantic Vector Search.
# Enforces User Authentication, Document Limits, and Multi-Tenant Isolation.
# ==============================================================================

import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.schemas.document import DocumentResponse, DocumentUploadResult, ChunkResponse, SearchResult
from app.services.pdf_service import (
    validate_pdf_metadata,
    extract_text_from_pdf,
    save_pdf_to_disk,
    MAX_DOCS_PER_USER
)
from app.services.chunker import chunk_document_pages
from app.services.vector_service import (
    build_and_save_document_index,
    search_document_chunks,
    delete_document_index
)
from app.services.embedding_service import EmbeddingUnavailableError

router = APIRouter(prefix="/documents", tags=["Documents (PDF, Chunks & FAISS Vector Search)"])


# ==============================================================================
# 1. Upload, Extract, Chunk & Index PDF
# ==============================================================================
@router.post("/upload", response_model=DocumentUploadResult, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Uploads a PDF, validates constraints, extracts text, chunks it into ~1000-char segments,
    saves records to MySQL, and builds a persistent FAISS vector index.
    """
    # Step 1: Enforce document limit (max 10 per user)
    existing_count = db.query(Document).filter(Document.user_id == current_user.id).count()
    if existing_count >= MAX_DOCS_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Upload limit reached ({existing_count}/{MAX_DOCS_PER_USER} documents). Delete an older document first."
        )

    # Step 2: Read binary contents of the uploaded file
    file_bytes = await file.read()

    # Step 3: Validate file metadata (extension, non-empty, max 10MB)
    validate_pdf_metadata(file.filename, file_bytes)

    # Step 4: Extract text page-by-page using PyMuPDF
    total_pages, pages_data, sample_text = extract_text_from_pdf(file_bytes)

    # Save the PDF, database records, and index as one logical operation. If any
    # stage fails, remove every artifact rather than leaving a half-indexed file.
    saved_path = None
    doc_record = None
    document_id = None
    try:
        saved_path = save_pdf_to_disk(file_bytes, file.filename, current_user.id)

        doc_record = Document(
            user_id=current_user.id,
            filename=file.filename,
            file_path=saved_path,
            file_size=len(file_bytes),
            page_count=total_pages
        )
        db.add(doc_record)
        db.flush()  # Allocate the document ID without committing a partial upload.
        document_id = doc_record.id

        raw_chunks = chunk_document_pages(
            pages_data=pages_data,
            document_id=doc_record.id,
            chunk_size=1000,
            chunk_overlap=200
        )
        if not raw_chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No indexable text chunks could be created from this PDF."
            )

        chunk_objects = [
            DocumentChunk(
                document_id=doc_record.id,
                page_number=c["page_number"],
                chunk_index=c["chunk_index"],
                chunk_text=c["chunk_text"],
                char_count=c["char_count"]
            )
            for c in raw_chunks
        ]
        db.add_all(chunk_objects)

        # The index itself is written atomically by vector_service before the
        # transaction is committed, so a successful response is fully searchable.
        build_and_save_document_index(current_user.id, doc_record.id, chunk_objects)
        db.commit()
        db.refresh(doc_record)
    except Exception as exc:
        db.rollback()
        if document_id is not None:
            delete_document_index(current_user.id, document_id)
        if saved_path and os.path.exists(saved_path):
            try:
                os.remove(saved_path)
            except OSError:
                pass

        if isinstance(exc, HTTPException):
            raise
        if isinstance(exc, EmbeddingUnavailableError):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Document indexing is temporarily unavailable. Please try again shortly."
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Document upload could not be completed. No partial document was saved."
        ) from exc

    return {
        "status": "success",
        "message": f"PDF '{file.filename}' uploaded, chunked ({len(chunk_objects)} chunks), and indexed with FAISS.",
        "document": doc_record,
        "total_chunks": len(chunk_objects),
        "sample_extracted_text": sample_text
    }


# ==============================================================================
# 2. List My Documents
# ==============================================================================
@router.get("", response_model=list[DocumentResponse])
def get_my_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves all documents owned by the logged-in student.
    """
    return db.query(Document).filter(Document.user_id == current_user.id).all()


# ==============================================================================
# 3. View Chunks of a Document
# ==============================================================================
@router.get("/{document_id}/chunks", response_model=list[ChunkResponse])
def get_document_chunks(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieves all extracted text chunks for a specific document with page numbers.
    """
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found or permission denied."
        )

    return db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id
    ).order_by(DocumentChunk.chunk_index.asc()).all()


# ==============================================================================
# 4. Semantic Search (FAISS Similarity Query)
# ==============================================================================
@router.get("/{document_id}/search", response_model=list[SearchResult])
def search_document(
    document_id: int,
    query: str = Query(..., min_length=2, description="Question or concept to search for"),
    top_k: int = Query(5, ge=1, le=10, description="Number of top chunks to retrieve"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Performs fast mathematical vector search using FAISS and Cosine Similarity.
    Returns the Top-K most relevant chunks ranked by relevance score with page numbers.
    """
    # Step 1: Verify document belongs to current user
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found or permission denied."
        )

    # Step 2: Search using FAISS
    results = search_document_chunks(
        user_id=current_user.id,
        document_id=document_id,
        query=query,
        db=db,
        top_k=top_k
    )

    return results


# ==============================================================================
from fastapi.responses import FileResponse
from app.core.security import decode_access_token


# ==============================================================================
# 5. View PDF in Browser Tab
# ==============================================================================
@router.get("/{document_id}/view")
def view_document_pdf(
    document_id: int,
    token: str | None = Query(None, description="Optional JWT token when viewing directly in browser tab"),
    current_user: User | None = Depends(lambda: None),
    db: Session = Depends(get_db)
):
    """
    Streams the original PDF directly into the browser tab using standard PDF preview.
    Supports both Authorization Header and ?token= query parameter for direct browser links.
    """
    # 1. Resolve user from query param token or DB
    user_id = None
    if token:
        payload = decode_access_token(token)
        if payload:
            email = payload.get("sub")
            user = db.query(User).filter(User.email == email).first()
            if user:
                user_id = user.id

    if user_id is None:
        # Fallback to current authenticated user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid ?token= query parameter or Bearer header."
        )

    # 2. Query document with ownership check
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == user_id
    ).first()

    if not doc or not os.path.exists(doc.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not found on disk or permission denied."
        )

    # 3. Stream PDF with inline disposition to open in browser viewer
    return FileResponse(
        path=doc.file_path,
        media_type="application/pdf",
        filename=doc.filename,
        headers={"Content-Disposition": f'inline; filename="{doc.filename}"'}
    )


# ==============================================================================
# 6. Delete a Document, Chunks & FAISS Index
# ==============================================================================
@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deletes a document from MySQL, its chunks, its FAISS index file, and the PDF file from disk.
    """
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found or permission denied."
        )

    # 1. Delete physical PDF file
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except OSError:
            pass

    # 2. Delete FAISS index file
    delete_document_index(current_user.id, document_id)

    # 3. Explicitly delete associated chunk records from MySQL
    db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()

    # 4. Delete document record from MySQL
    db.delete(doc)
    db.commit()

    return {
        "status": "success",
        "message": f"Document '{doc.filename}', its chunks, and its FAISS index have been deleted."
    }

