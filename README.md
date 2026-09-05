# 🎓 Study With AI — Autonomous Academic RAG & Study Assistant

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1.svg?style=flat&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![FAISS](https://img.shields.io/badge/FAISS-Vector%20Search-orange.svg?style=flat)](https://github.com/facebookresearch/faiss)
[![Gemini](https://img.shields.io/badge/Google%20Gemini-3.6%20Flash-4285F4.svg?style=flat&logo=google&logoColor=white)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> An enterprise-grade, multi-tenant academic study platform that transforms dense textbook PDFs into verified, interactive study tools—combining **Retrieval-Augmented Generation (RAG)**, local vector search, active-recall flashcards, self-grading quizzes, condensed exam cheat sheets, and visual concept flowcharts.

---

## 🌟 The Problem & The Solution

### The Problem with Generic LLMs in Education
When students study using generic AI tools (like raw ChatGPT):
1. **Hallucination Risk**: LLMs generate plausible-sounding but completely incorrect facts.
2. **No Verifiability**: They cannot point to the exact textbook page prescribed in the university syllabus.
3. **Context Window Limitations**: Slicing entire 100-page textbooks directly into an LLM prompt is slow, expensive, and exceeds token budgets.

### The "Study With AI" Solution
**Study With AI** enforces strict **Retrieval-Augmented Generation (RAG)**:
- Reads and parses the student’s actual PDF textbook.
- Indexes paragraphs with high-dimensional vector embeddings.
- Retrieves only the exact relevant passages when a student asks questions or studies concepts.
- Generates verified answers and revision materials strictly grounded in the document with **exact page citations** (e.g. `[Biology.pdf — Page 14]`).

---

## 🎯 The 5 Core AI Study Tools

| # | Tool | Endpoint | Client Micro-Module | Description |
|---|---|---|---|---|
| 1 | **Ask AI (RAG Q&A)** | `POST /documents/{id}/ask` | `qa.js` | Top-K FAISS retrieval + lost-in-the-middle reordering + grounded LLM response with verifiable `[Page X]` citations. |
| 2 | **Active-Recall Flashcards** | `POST /documents/{id}/flashcards` | `flashcards.js` | Interactive 3D CSS card flip deck with shuffle, single-card navigation, and grid overview mode. |
| 3 | **Practice Quiz** | `POST /documents/{id}/quiz` | `quiz.js` | Step-by-step 4-option MCQ engine with back navigation allowed, single attempt locking (strict no-retake), and instant answers review. |
| 4 | **1-Page Exam Cheat Sheet** | `POST /documents/{id}/summary` | `summary.js` | Condenses dense chapters into 4 clean blocks: Executive Overview, Key Takeaways, Core Definitions with page numbers, and Common Exam Traps. |
| 5 | **Visual Concept Mind Map** | `POST /documents/{id}/mindmap` | `mindmap.js` | AI concept hierarchy rendered as an interactive top-down (`graph TD`) SVG flowchart via **Mermaid.js** with zero server GPU overhead. |

---

## 🏛️ System Architecture

```
[ Frontend: Modular Micro-Services (Vanilla JS + HTML5 + CSS3) ]
  ├── config.js     (Global state & endpoints)
  ├── auth.js       (JWT login / register / eye toggles)
  ├── documents.js  (Upload, delete, view PDF stream)
  ├── qa.js         (Tool 1: Ask AI RAG chat)
  ├── flashcards.js (Tool 2: 3D interactive flip deck)
  ├── quiz.js       (Tool 3: Step-by-step 4-option MCQ)
  ├── summary.js    (Tool 4: 1-Page Exam Cheat Sheet)
  └── mindmap.js    (Tool 5: Mermaid.js visual flowchart)
                              │  HTTP / JWT Bearer
                              ▼
[ Backend: FastAPI (Python 3.12+) ]
  ├── Document Engine: PyMuPDF (extraction, noise filter, de-hyphenation)
  ├── Chunker Engine:  ~1000 chars, 200 overlap, word-boundary snapping
  ├── Vector Engine:   FAISS IndexIDMap2 + FlatIP (Normalized Cosine Similarity)
  ├── AI Orchestrator: Universal LLM Client (Gemini 3.6 Flash / OpenAI gpt-4o-mini)
  │                    with Local Grounded Dynamic Synthesis Fallback
  └── In-Memory Cache: Thread-safe LRU caches for query embeddings & FAISS indices
                              │
               ┌──────────────┴──────────────┐
               ▼                             ▼
       [ MySQL Database ]            [ Local Disk Storage ]
       - users (Bcrypt passwords)    - uploads/{user_id}/<uuid>_<filename>.pdf
       - documents (metadata)        - indexes/{user_id}/<doc_id>.faiss
       - document_chunks             - indexes/{user_id}/<doc_id>.meta.json
```

---

## 🛡️ Key Engineering Highlights & Best Practices

1. **Multi-Tenant Security & Strict Data Isolation**:
   - Every database query strictly filters by `Document.user_id == current_user.id`. Cross-tenant access returns HTTP 404/403.
   - Uploads and FAISS vector indexes are partitioned into isolated per-user directories (`uploads/{user_id}/` and `indexes/{user_id}/`).
2. **Noise-Filtered PDF Extraction**:
   - Automatically detects and eliminates running headers and footers that repeat across $\ge 60\%$ of pages.
   - Re-stitches hyphenated line breaks (`pro-` / `cess` $\rightarrow$ `process`) and extracts text blocks in natural reading order (`sort=True`).
3. **Word-Boundary Aware Chunking**:
   - Sliding window overlap snaps to whole word boundaries (`next_space + 1`), preventing chunks from starting with sliced half-words.
4. **Dual-Provider Embedding Profiles**:
   - Gemini embedding model backed by a real local **`sentence-transformers/all-MiniLM-L6-v2`** model running on CPU.
   - Strict vector space separation managed by an immutable `EmbeddingProfile` prevents dimension collisions.
5. **Anti-Hallucination Guardrails**:
   - Enforces `MIN_RETRIEVAL_SCORE = 0.35` to immediately refuse unrelated questions rather than feeding garbage to the LLM.
   - Page citations are verified against `allowed_page_numbers` present in retrieved chunks.
6. **Rate-Limit Resilience (Zero-Crash Architecture)**:
   - Built-in automatic retry loop with exponential backoff for transient `429 RESOURCE_EXHAUSTED` / `503 UNAVAILABLE` API spikes.
   - Dynamic question-aware textbook synthesis engine ensures the application continues serving grounded answers even during complete external cloud API outages.
7. **In-Memory LRU Caching**:
   - Bounded thread-safe caches keep active FAISS indices and query embeddings in RAM, reducing search latency to **< 2ms**.
8. **Transactional Atomic Upload Rollback**:
   - Coordinated `try/except` transaction cleanup: if PDF parsing, chunking, or FAISS indexing fails, any written disk files and database rows are purged immediately, leaving zero orphaned artifacts.

---

## 🛠️ Tech Stack

* **Backend**: FastAPI, Uvicorn, Python 3.12+
* **Database & ORM**: MySQL 8.0, SQLAlchemy 2.0, PyMySQL
* **Authentication**: PyJWT (HS256 Bearer Tokens), Passlib / Bcrypt
* **PDF & Text Extraction**: PyMuPDF (`fitz`), Unicode NFKC normalization, Regex
* **Vector Search & AI**: FAISS (`faiss-cpu`), Sentence-Transformers (`all-MiniLM-L6-v2`), NumPy
* **LLM Engine**: Google Gemini 3.6 Flash (`google-genai`), OpenAI `gpt-4o-mini` (`httpx`)
* **Frontend**: Vanilla JavaScript (ES6+ Modular Micro-Services), HTML5, CSS3 (3D Card Flip animations)
* **Client-Side Rendering**: Mermaid.js v10 (SVG concept flowcharts), Marked.js (Markdown rendering)

---

## 🚀 Getting Started

### 1. Prerequisites
* Python 3.12 or higher
* MySQL Server 8.0+ running locally or in Docker

### 2. Clone the Repository
```bash
git clone https://github.com/your-username/study-with-ai.git
cd study-with-ai
```

### 3. Set Up Virtual Environment
```bash
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your details:
```bash
cp .env.example .env
```

Edit `.env`:
```env
PROJECT_NAME="Study With AI"
PORT=8000
DATABASE_URL="mysql+pymysql://root:password@localhost:3306/study_with_ai"

# Gemini API Key (Get a free key from https://aistudio.google.com/)
GEMINI_API_KEY="your-gemini-api-key"

# JWT Security
SECRET_KEY="your-super-secret-jwt-key"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### 6. Initialize Database
Ensure MySQL is running, then create the database:
```sql
CREATE DATABASE study_with_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
*(Tables are automatically created by SQLAlchemy upon first server boot.)*

### 7. Run the Application
```bash
uvicorn main:app --reload --port 8000
```

Open your browser at **`http://localhost:8000/`**.  
Interactive Swagger API documentation is available at **`http://localhost:8000/docs`**.

---

## 📁 Project Structure

```
study-with-ai/
├── app/
│   ├── api/
│   │   ├── auth.py              # User registration, login, JWT token issue
│   │   ├── documents.py         # PDF upload, listing, stream viewing, deletion
│   │   ├── rag.py               # Ask AI RAG Q&A endpoint
│   │   └── study_tools.py       # Flashcards, Quiz, Summary, and Mindmap endpoints
│   ├── core/
│   │   ├── config.py            # Environment settings and constants
│   │   ├── database.py          # SQLAlchemy engine & session factory
│   │   ├── dependencies.py      # JWT authentication dependency injection
│   │   └── security.py          # Bcrypt password hashing & JWT encoding/decoding
│   ├── models/
│   │   ├── user.py              # User SQL table model
│   │   ├── document.py          # Document metadata SQL table model
│   │   └── chunk.py             # DocumentChunk SQL table model
│   ├── schemas/
│   │   ├── user.py              # Auth request/response Pydantic models
│   │   ├── document.py          # Document upload/search Pydantic models
│   │   ├── rag.py               # Q&A request/response Pydantic models
│   │   └── study_tools.py       # Study suite Pydantic models
│   └── services/
│       ├── chunker.py           # Word-boundary sliding window text chunker
│       ├── embedding_service.py # Gemini & SentenceTransformer vector embedder
│       ├── gemini_service.py    # Universal LLM client & rate-limit fallback
│       ├── pdf_service.py       # PyMuPDF extraction, noise removal & normalization
│       ├── prompt_templates.py  # Structured XML prompts & system instructions
│       ├── rag_service.py       # RAG pipeline orchestrator & lost-in-the-middle
│       ├── study_tools_service.py # Flashcards, Quiz, Summary, and Mindmap generator
│       └── vector_service.py    # FAISS IndexIDMap2 manager & in-memory cache
├── static/
│   ├── index.html               # Main Single-Page Application (SPA) layout
│   ├── style.css                # Custom styling, 3D card flips & layout
│   └── js/                      # Decoupled Frontend Micro-Services
│       ├── config.js            # Shared global state & API config
│       ├── auth.js              # Sign in, register, eye toggles, token storage
│       ├── documents.js         # PDF uploads, dropdown, active doc, deletion
│       ├── qa.js                # Ask AI chat controller
│       ├── flashcards.js        # 3D interactive flashcards controller
│       ├── quiz.js              # Step-by-step practice quiz controller
│       ├── summary.js           # 1-Page Exam Cheat Sheet controller
│       ├── mindmap.js           # Mermaid.js SVG flowchart controller
│       └── app.js               # Application bootstrapper & tab router
├── indexes/                     # Partitioned FAISS vector storage (ignored in git)
├── uploads/                     # Partitioned PDF storage (ignored in git)
├── .env.example                 # Environment variables template
├── .gitignore                   # Git exclusion rules
├── main.py                      # FastAPI application entrypoint
└── requirements.txt             # Python dependencies
```

---

## 📜 License
Distributed under the MIT License. See `LICENSE` for more information.