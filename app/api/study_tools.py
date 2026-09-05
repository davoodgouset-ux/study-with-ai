# ==============================================================================
# File: app/api/study_tools.py
# Purpose: API Endpoints for AI Study Tools:
# 1. POST /documents/{id}/flashcards - Active-Recall Flashcards
# 2. POST /documents/{id}/quiz       - 4-Option Practice Quizzes
# 3. POST /documents/{id}/summary    - 1-Page Exam Cheat Sheet
# 4. POST /documents/{id}/mindmap    - Visual Concept Mind Map (Mermaid.js)
# ==============================================================================

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.study_tools import (
    FlashcardsResponse,
    QuizResponse,
    ExamSummaryResponse,
    MindMapResponse
)
from app.services.study_tools_service import (
    generate_flashcards_for_document,
    generate_quiz_for_document,
    generate_summary_for_document,
    generate_mindmap_for_document
)

router = APIRouter(prefix="/documents", tags=["AI Study Tools (Flashcards, Quizzes & Summaries)"])


@router.post(
    "/{document_id}/flashcards",
    response_model=FlashcardsResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Active-Recall Flashcards"
)
def get_flashcards(
    document_id: int,
    count: int = Query(5, ge=1, le=10, description="Number of flashcards to generate"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generates digital active-recall flashcards from an uploaded textbook.
    Each flashcard includes front question, back answer, and exact page citation.
    """
    return generate_flashcards_for_document(
        user_id=current_user.id,
        document_id=document_id,
        count=count,
        db=db
    )


@router.post(
    "/{document_id}/quiz",
    response_model=QuizResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Multiple-Choice Practice Quiz"
)
def get_practice_quiz(
    document_id: int,
    count: int = Query(5, ge=1, le=10, description="Number of multiple-choice questions"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generates a 4-option multiple-choice practice quiz with correct answer indices,
    educational explanations, and textbook page references.
    """
    return generate_quiz_for_document(
        user_id=current_user.id,
        document_id=document_id,
        count=count,
        db=db
    )


@router.post(
    "/{document_id}/summary",
    response_model=ExamSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate 1-Page Exam Revision Cheat Sheet"
)
def get_exam_summary(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generates a condensed 1-page exam revision cheat sheet containing:
    - Executive chapter overview
    - Bulleted key takeaways
    - Core definitions with page citations
    - Common exam pitfalls & misconceptions to avoid
    """
    return generate_summary_for_document(
        user_id=current_user.id,
        document_id=document_id,
        db=db
    )


@router.post(
    "/{document_id}/mindmap",
    response_model=MindMapResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Visual Concept Mind Map (Mermaid.js)"
)
def get_concept_mindmap(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generates a hierarchical visual concept mind map with executable Mermaid.js flowchart code.
    """
    return generate_mindmap_for_document(
        user_id=current_user.id,
        document_id=document_id,
        db=db
    )
