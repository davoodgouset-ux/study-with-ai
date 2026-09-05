# ==============================================================================
# File: app/services/study_tools_service.py
# Purpose: AI Study Tools Orchestrator:
# Generates Flashcards, Practice Quizzes, 1-Page Exam Summaries, and Visual Mind Maps
# from textbook chunks using Google Gemini 3.6 Flash.
# ZERO hardcoded topics: All content is dynamically generated strictly from the user's uploaded PDF!
# ==============================================================================

import re
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Document, DocumentChunk
from app.services.gemini_service import generate_structured_json
from app.services.prompt_templates import (
    build_flashcards_prompt,
    build_quiz_prompt,
    build_exam_summary_prompt,
    build_mindmap_prompt
)


def get_verified_document_chunks(user_id: int, document_id: int, db: Session) -> tuple[Document, list[dict]]:
    """
    Security Layer: Verifies document ownership and retrieves all text chunks from MySQL.
    Strictly isolated to user_id.
    """
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == user_id
    ).first()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} was not found or access is denied."
        )

    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id
    ).order_by(DocumentChunk.chunk_index.asc()).all()

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document '{doc.filename}' has no extracted chunks."
        )

    formatted_chunks = [
        {
            "chunk_index": c.chunk_index,
            "page_number": c.page_number,
            "chunk_text": c.chunk_text
        }
        for c in chunks
    ]
    return doc, formatted_chunks


def _extract_dynamic_fallback_flashcards(doc: Document, chunks: list[dict], count: int) -> list[dict]:
    """
    Extracts active-recall flashcards dynamically from the user's actual document chunks.
    Ensures ZERO cross-document contamination when running without LLM or on LLM rate-limit.
    """
    cards = []
    for idx, c in enumerate(chunks[:count], start=1):
        text = c.get("chunk_text", "").strip()
        page = c.get("page_number", 1)
        
        # Split into sentences
        sentences = [s.strip() for s in re.split(r'[.!?]\s+', text) if len(s.strip()) > 15]
        
        if sentences:
            q_text = f"Key Concept ({doc.filename} - Section {idx}): What is the primary takeaway regarding '{sentences[0][:60]}...'?"
            a_text = " ".join(sentences[:2]) if len(sentences) > 1 else sentences[0]
        else:
            q_text = f"Review Concept from Section {idx}"
            a_text = text[:200]
            
        cards.append({
            "id": idx,
            "front_question": q_text,
            "back_answer": a_text,
            "page_citation": f"{doc.filename} — Page {page}"
        })
    return cards


def generate_flashcards_for_document(
    user_id: int,
    document_id: int,
    count: int,
    db: Session
) -> dict:
    """
    Generates high-yield active-recall digital study flashcards strictly from the user's PDF.
    """
    doc, chunks = get_verified_document_chunks(user_id, document_id, db)

    # Limit context to top 15 chunks
    selected_chunks = chunks[:15]
    prompt = build_flashcards_prompt(doc.filename, selected_chunks, count=count)

    raw_data, model_name = generate_structured_json(prompt)

    # Check if LLM returned structured flashcards
    cards_list = None
    if isinstance(raw_data, dict) and "flashcards" in raw_data and isinstance(raw_data["flashcards"], list) and len(raw_data["flashcards"]) > 0:
        cards_list = raw_data["flashcards"]
    elif isinstance(raw_data, list) and len(raw_data) > 0 and isinstance(raw_data[0], dict) and "front_question" in raw_data[0]:
        cards_list = raw_data

    # If LLM did not return structured cards, dynamically generate from the actual PDF chunks
    if not cards_list:
        cards_list = _extract_dynamic_fallback_flashcards(doc, selected_chunks, count)

    # Validate and clean items
    cleaned_cards = []
    for idx, item in enumerate(cards_list, start=1):
        cleaned_cards.append({
            "id": item.get("id", idx),
            "front_question": item.get("front_question", item.get("question", f"Concept {idx}")),
            "back_answer": item.get("back_answer", item.get("answer", "Explanation from document.")),
            "page_citation": item.get("page_citation", f"{doc.filename} — Page 1")
        })

    return {
        "document_id": doc.id,
        "document_filename": doc.filename,
        "total_cards": len(cleaned_cards),
        "flashcards": cleaned_cards,
        "model_used": model_name
    }


def generate_quiz_for_document(
    user_id: int,
    document_id: int,
    count: int,
    db: Session
) -> dict:
    """
    Generates 4-option multiple-choice practice questions strictly from the user's PDF.
    """
    doc, chunks = get_verified_document_chunks(user_id, document_id, db)

    selected_chunks = chunks[:15]
    prompt = build_quiz_prompt(doc.filename, selected_chunks, count=count)

    raw_data, model_name = generate_structured_json(prompt)

    q_list = None
    if isinstance(raw_data, dict) and "questions" in raw_data and isinstance(raw_data["questions"], list) and len(raw_data["questions"]) > 0:
        q_list = raw_data["questions"]
    elif isinstance(raw_data, list) and len(raw_data) > 0:
        q_list = raw_data

    # Dynamic fallback from actual chunks
    if not q_list:
        q_list = []
        for idx, c in enumerate(selected_chunks[:count], start=1):
            text = c.get("chunk_text", "")
            page = c.get("page_number", 1)
            sentences = [s.strip() for s in re.split(r'[.!?]\s+', text) if len(s.strip()) > 15]
            correct = sentences[0] if sentences else f"Key concept from {doc.filename}"
            q_list.append({
                "id": idx,
                "question": f"According to {doc.filename} (Page {page}), which of the following statements is correct?",
                "options": [
                    correct,
                    f"Contradictory statement to concept {idx}",
                    f"Unrelated premise regarding section {idx}",
                    "None of the above"
                ],
                "correct_answer": correct,
                "correct_option_index": 0,
                "explanation": f"Grounded directly in text on Page {page}.",
                "page_citation": f"{doc.filename} — Page {page}"
            })

    cleaned_questions = []
    for idx, item in enumerate(q_list, start=1):
        opts = item.get("options", ["Option A", "Option B", "Option C", "Option D"])
        while len(opts) < 4:
            opts.append(f"Option {chr(65 + len(opts))}")
        opts = opts[:4]

        correct_idx = item.get("correct_option_index", 0)
        if not (0 <= correct_idx <= 3):
            correct_idx = 0

        correct_ans = item.get("correct_answer", opts[correct_idx])

        cleaned_questions.append({
            "id": item.get("id", idx),
            "question": item.get("question", "Study Question"),
            "options": opts,
            "correct_answer": correct_ans,
            "correct_option_index": correct_idx,
            "explanation": item.get("explanation", f"Based on {doc.filename}."),
            "page_citation": item.get("page_citation", f"{doc.filename} — Page 1")
        })

    return {
        "document_id": doc.id,
        "document_filename": doc.filename,
        "total_questions": len(cleaned_questions),
        "questions": cleaned_questions,
        "model_used": model_name
    }


def generate_summary_for_document(
    user_id: int,
    document_id: int,
    db: Session
) -> dict:
    """
    Generates a 1-page condensed exam revision sheet strictly from the user's PDF.
    """
    doc, chunks = get_verified_document_chunks(user_id, document_id, db)

    selected_chunks = chunks[:20]
    prompt = build_exam_summary_prompt(doc.filename, selected_chunks)

    raw_data, model_name = generate_structured_json(prompt)

    if not isinstance(raw_data, dict) or "overview" not in raw_data or raw_data.get("fallback"):
        # Dynamic extraction from user's chunks
        sample_sentences = []
        for c in selected_chunks[:5]:
            s_list = [s.strip() for s in re.split(r'[.!?]\s+', c.get("chunk_text", "")) if len(s.strip()) > 20]
            if s_list:
                sample_sentences.append(s_list[0])

        raw_data = {
            "summary_title": f"1-Page Exam Cheat Sheet: {doc.filename}",
            "overview": f"Comprehensive study summary compiled directly from '{doc.filename}'.",
            "key_takeaways": sample_sentences[:4] if sample_sentences else [f"Core material from {doc.filename}"],
            "core_definitions": [
                {"term": f"Section {i+1} Topic", "definition": s[:120], "page": f"Page {selected_chunks[i]['page_number']}"}
                for i, s in enumerate(sample_sentences[:3])
            ],
            "common_exam_traps": [
                f"Ensure accurate distinction between concepts highlighted in {doc.filename}."
            ],
            "page_citations": [f"{doc.filename} — Page {c['page_number']}" for c in selected_chunks[:3]]
        }

    return {
        "document_id": doc.id,
        "document_filename": doc.filename,
        "summary_title": raw_data.get("summary_title", f"1-Page Exam Cheat Sheet: {doc.filename}"),
        "overview": raw_data.get("overview", f"Overview of {doc.filename}"),
        "key_takeaways": raw_data.get("key_takeaways", []),
        "core_definitions": raw_data.get("core_definitions", []),
        "common_exam_traps": raw_data.get("common_exam_traps", []),
        "page_citations": raw_data.get("page_citations", [f"{doc.filename} — Page 1"]),
        "model_used": model_name
    }


def _clean_node_text(raw_text: str, max_len: int = 35) -> str:
    """
    Strips raw filename citations, parentheses, and illegal Mermaid punctuation.
    """
    cleaned = re.sub(r'\[.*?\]|\(.*?\)|[a-zA-Z0-9_\-]+\.pdf', '', str(raw_text))
    cleaned = re.sub(r'["\[\](){}<>;|]', '', cleaned).strip()
    return cleaned[:max_len] if cleaned else "Key Concept"


def _build_clean_mermaid_diagram(root_concept: str, nodes: list) -> str:
    """
    Builds 100% valid, error-free Mermaid.js flowchart code from root and node hierarchy.
    Sanitizes special characters to prevent diagram syntax errors.
    """
    clean_root = _clean_node_text(root_concept, max_len=30)

    lines = ["graph TD", f'  Root["{clean_root}"]']
    for i, node in enumerate(nodes[:5], start=1):
        raw_topic = node.get("topic", f"Topic {i}") if isinstance(node, dict) else str(node)
        topic = _clean_node_text(raw_topic, max_len=35)
        lines.append(f'  Root --> T{i}["{topic}"]')

        subtopics = node.get("subtopics", []) if isinstance(node, dict) else []
        for j, sub in enumerate(subtopics[:4], start=1):
            sub_clean = _clean_node_text(sub, max_len=40)
            lines.append(f'  T{i} --> S{i}_{j}["{sub_clean}"]')

    return "\n".join(lines)


def generate_mindmap_for_document(
    user_id: int,
    document_id: int,
    db: Session
) -> dict:
    """
    Generates visual concept hierarchy strictly from the user's PDF.
    """
    doc, chunks = get_verified_document_chunks(user_id, document_id, db)

    selected_chunks = chunks[:20]
    prompt = build_mindmap_prompt(doc.filename, selected_chunks)

    raw_data, model_name = generate_structured_json(prompt)

    root_concept = None
    nodes = []

    if isinstance(raw_data, dict) and not raw_data.get("fallback"):
        root_concept = raw_data.get("root_concept")
        if isinstance(raw_data.get("nodes"), list):
            nodes = raw_data["nodes"]

    if not root_concept:
        root_concept = re.sub(r'[^a-zA-Z0-9 ]', '', doc.filename.replace('.pdf', '')).strip()[:30] or "Core Concepts"

    # Fallback to document chunks if nodes are missing or empty
    if not isinstance(nodes, list) or len(nodes) == 0:
        nodes = []
        for i, c in enumerate(selected_chunks[:4], start=1):
            sentences = [s.strip() for s in re.split(r'[.!?\n]\s*', c.get("chunk_text", "")) if len(s.strip()) > 15]
            topic_name = sentences[0][:35] if sentences else f"Section {i} (Page {c['page_number']})"
            sub_items = [s[:40] for s in sentences[1:3]] if len(sentences) > 1 else [f"Detail from Page {c['page_number']}"]
            nodes.append({
                "topic": topic_name,
                "subtopics": sub_items
            })

    # Generate 100% syntactically valid Mermaid code
    mermaid_code = _build_clean_mermaid_diagram(root_concept, nodes)

    return {
        "document_id": doc.id,
        "document_filename": doc.filename,
        "root_concept": root_concept,
        "nodes": nodes,
        "mermaid_code": mermaid_code,
        "model_used": model_name
    }
