# ==============================================================================
# File: ask_ai_chat.py
# Purpose: Interactive live terminal chat with your uploaded PDF textbook.
# ==============================================================================

import sys
sys.stdout.reconfigure(encoding='utf-8')

from app.core.database import SessionLocal
from app.models import Document
from app.services.rag_service import answer_question_about_document

db = SessionLocal()

# Load the latest textbook (Doc ID 4)
doc = db.query(Document).filter(Document.id == 4).first()
if not doc:
    doc = db.query(Document).order_by(Document.id.desc()).first()

print("=" * 75)
print(f"       STUDY WITH AI — LIVE TERMINAL TUTOR (Doc #{doc.id}: {doc.filename})")
print("=" * 75)

# Example questions you can ask
test_questions = [
    "What are CPU scheduling algorithms like Round Robin?",
    "Explain virtual memory and page replacement",
    "What are the four necessary conditions for deadlocks?"
]

for i, q in enumerate(test_questions, 1):
    print(f"\n[STUDENT QUESTION #{i}]: {q}")
    print("-" * 75)
    
    res = answer_question_about_document(
        user_id=doc.user_id,
        document_id=doc.id,
        question=q,
        db=db,
        top_k=3
    )
    
    print("[GEMINI 3.6 FLASH ANSWER]:")
    print(res['answer'])
    print(f"\n>> Citations Detected : {res['citations']}")
    print(f">> Model Used         : {res['model_used']}")
    print("=" * 75)

db.close()
