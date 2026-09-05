# ==============================================================================
# File: test_faiss_realtime.py
# Purpose: Real-time visual demonstration of FAISS Cosine Similarity search on your laptop.
# Shows exact timing in milliseconds, similarity scores, and page citations.
# ==============================================================================

import time
import sys

# Force UTF-8 stdout for Windows consoles
sys.stdout.reconfigure(encoding='utf-8')

from app.core.database import SessionLocal
from app.models import User, Document, DocumentChunk
from app.services.vector_service import search_document_chunks

# Open DB session
db = SessionLocal()

# User 4 has our sample operating systems textbook (Doc ID: 4)
user_id = 4
document_id = 4

# Try 3 different real-time student questions!
sample_queries = [
    "What is Round Robin and CPU scheduling?",
    "Explain virtual memory and page replacement algorithms",
    "What are the four conditions that lead to a deadlock?"
]

print("=" * 80)
print("       REAL-TIME FAISS VECTOR SEARCH BENCHMARK ON YOUR LAPTOP")
print("=" * 80)

for q_idx, query in enumerate(sample_queries, start=1):
    print(f"\n[QUERY #{q_idx}]: \"{query}\"")
    print("-" * 80)

    # Measure real-time execution in milliseconds
    start_time = time.perf_counter()
    results = search_document_chunks(user_id=user_id, document_id=document_id, query=query, db=db, top_k=3)
    elapsed_ms = (time.perf_counter() - start_time) * 1000

    print(f">> Search Completed in: {elapsed_ms:.2f} milliseconds!")
    print("Top Retrieved Matches (Ranked by Cosine Relevance):")

    for r in results:
        rank = r['rank']
        score = r['score']
        page = r['page_number']
        snippet = r['chunk_text'][:90].replace('\n', ' ')
        print(f"  Rank #{rank} | Score: {score:+.4f} | Citation: [Page {page}]")
        print(f"          Snippet: \"{snippet}...\"\n")

db.close()
print("=" * 80)
