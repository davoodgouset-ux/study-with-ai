# ==============================================================================
# File: app/schemas/study_tools.py
# Purpose: Pydantic schemas for AI Study Tools:
# 1. Active-Recall Flashcards
# 2. Multiple-Choice Practice Quizzes
# 3. 1-Page Exam Cheat Sheet / Chapter Summaries
# 4. Visual Concept Mind Maps (Mermaid.js)
# ==============================================================================

from pydantic import BaseModel, Field
from typing import List, Optional


# ==============================================================================
# 1. Flashcards Schemas
# ==============================================================================
class FlashcardItem(BaseModel):
    """
    A single digital active-recall study flashcard.
    """
    id: int = Field(..., description="Unique sequence number of the card")
    front_question: str = Field(..., description="Core concept or question to test memory")
    back_answer: str = Field(..., description="Concise, clear definition or answer")
    page_citation: str = Field(..., description="Exact page reference in uploaded textbook")


class FlashcardsResponse(BaseModel):
    """
    Response schema returning generated study flashcards.
    """
    document_id: int
    document_filename: str
    total_cards: int
    flashcards: List[FlashcardItem]
    model_used: str


# ==============================================================================
# 2. Practice Quiz Schemas
# ==============================================================================
class QuizQuestion(BaseModel):
    """
    A single 4-option multiple choice question with explanation.
    """
    id: int = Field(..., description="Question number (1, 2, 3...)")
    question: str = Field(..., description="The quiz question text")
    options: List[str] = Field(..., min_length=4, max_length=4, description="4 multiple-choice options (A, B, C, D)")
    correct_answer: str = Field(..., description="The exact correct option string")
    correct_option_index: int = Field(..., ge=0, le=3, description="Index of correct option: 0 for A, 1 for B, 2 for C, 3 for D")
    explanation: str = Field(..., description="Explanation of why the answer is correct and others are wrong")
    page_citation: str = Field(..., description="Source page reference in textbook")


class QuizResponse(BaseModel):
    """
    Response schema returning generated practice quiz questions.
    """
    document_id: int
    document_filename: str
    total_questions: int
    questions: List[QuizQuestion]
    model_used: str


# ==============================================================================
# 3. 1-Page Exam Summary Schemas
# ==============================================================================
class ExamSummaryResponse(BaseModel):
    """
    Response schema for 1-page condensed exam revision sheet.
    """
    document_id: int
    document_filename: str
    summary_title: str
    overview: str
    key_takeaways: List[str]
    core_definitions: List[dict]  # e.g. [{"term": "Deadlock", "definition": "...", "page": "Page 3"}]
    common_exam_traps: List[str]  # Common mistakes students make in exams
    page_citations: List[str]
    model_used: str


# ==============================================================================
# 4. Visual Concept Mind Map Schemas (Mermaid.js)
# ==============================================================================
class MindMapNode(BaseModel):
    """
    A node in the concept relationship graph.
    """
    topic: str
    subtopics: List[str]


class MindMapResponse(BaseModel):
    """
    Response schema returning visual concept hierarchy and Mermaid.js diagram code.
    """
    document_id: int
    document_filename: str
    root_concept: str
    nodes: List[MindMapNode]
    mermaid_code: str  # e.g. 'graph TD\n  OS["Operating System"] --> Process["Process Management"]'
    model_used: str
