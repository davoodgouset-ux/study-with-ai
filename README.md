# 🎓 Exam Prep AI: Question Paper Q&A Bot (RAG) & Multi-Modal Study Assistant
### *(Study With AI — Autonomous Academic Learning Platform)*

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-Render_Cloud-success?style=for-the-badge&logo=render)](https://study-with-ai-7x16.onrender.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0%20%2F%20TiDB-4479A1.svg?style=flat&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![FAISS](https://img.shields.io/badge/FAISS-Vector%20Search%20(<3ms)-orange.svg?style=flat)](https://github.com/facebookresearch/faiss)
[![Gemini](https://img.shields.io/badge/Google%20Gemini-3.6%20Flash-4285F4.svg?style=flat&logo=google&logoColor=white)](https://ai.google.dev/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🌐 Public Live Application

> ### 🔗 **Live Link**: [https://study-with-ai-7x16.onrender.com](https://study-with-ai-7x16.onrender.com)
> **Status**: 🟢 **Active & Deployed on Render.com**  
> *Students and evaluators can register, upload university question papers or syllabus textbooks in PDF, and access verified AI study tools with exact textbook page citations.*

---

## 📋 Academic Project Overview

* **Project Title**: Exam Prep AI: Question Paper Q&A Bot (RAG) & Multi-Modal Study Assistant
* **Project ID**: `Prj006`
* **Team ID**: `T006`
* **Institution**: **Kalasalingam Academy of Research and Education** *(Deemed to be University, Anand Nagar, Krishnankoil)*
* **Department**: Department of Computer Science and Engineering
* **Project Trainer / Guide**: **Mr. SHIRWIN PRINCE I** *(Assistant Professor, Dept. of CSE)*
* **Team GitHub Repository**: [https://github.com/davoodgouset-ux/study-with-ai](https://github.com/davoodgouset-ux/study-with-ai)

### 👥 Team Members

| # | Student Name | Registration Number | Individual GitHub Profile |
| :-: | :--- | :---: | :--- |
| 1 | **Tadipatri Davood Gouse** | `99230040061` | [![GitHub](https://img.shields.io/badge/GitHub-davoodgouset--ux-181717?logo=github)](https://github.com/davoodgouset-ux) |
| 2 | **Tholeti Harshavardhan** | `99230040065` | [![GitHub](https://img.shields.io/badge/GitHub-HarshaTholeti-181717?logo=github)](https://github.com/HarshaTholeti/IntelliLearn-AI) |
| 3 | **Yarraballa Sree Vardhan** | `99230040184` | [![GitHub](https://img.shields.io/badge/GitHub-SREEVARDHAN588-181717?logo=github)](https://github.com/SREEVARDHAN588/ExamPrep-AI-Question-Paper-Q-A-Bot) |
| 4 | **Duda Siddu** | `99230040018` | [![GitHub](https://img.shields.io/badge/GitHub-Siddu--hash--arch-181717?logo=github)](https://github.com/Siddu-hash-arch/study-with-ai) |

---

## 📑 Project Documentation & Presentation Downloads

All academic project submission artifacts are included in this repository:

1. 📄 **College Project Report Template (DOCX)**: [`Study_With_AI_Project_Report_Template.docx`](Study_With_AI_Project_Report_Template.docx)  
   *Formatted strictly according to the guide's 6-section template with student tables and figures.*
2. 📘 **Comprehensive 25-Page Project Thesis (DOCX)**: [`Study_With_AI_Project_Report.docx`](Study_With_AI_Project_Report.docx)  
   *Complete academic research documentation with mathematical formulations, literature survey, and 29 E2E test assertions.*
3. 📊 **PowerPoint Presentation Deck (PPTX)**: [`Study_With_AI_Presentation.pptx`](Study_With_AI_Presentation.pptx)  
   *14-slide widescreen presentation deck with embedded architecture diagrams and performance benchmark charts.*

---

## 🌟 The Problem & The Solution

### The Academic Problem
When university students prepare for examinations or navigate 800+ page technical textbooks:
1. **Cognitive Overload**: Sifting through dense syllabus PDFs and past question papers manually is time-consuming.
2. **LLM Hallucinations**: Standard AI chatbots (e.g., ChatGPT) generate plausible-sounding but factually ungrounded answers.
3. **Lack of Syllabus Verifiability**: Generic AI cannot pinpoint the exact textbook page prescribed by university grading rubrics.

### The RAG Solution
**Study With AI** decouples factual knowledge retrieval from language generation:
- Extracts text with **PyMuPDF**, automatically stripping running headers/footers ($\ge 60\%$ frequency) and repairing hyphenations.
- Enforces **adaptive word-boundary sliding window chunking** (1,000 chars, 200 overlap).
- Indexes text chunks into an in-memory **Meta FAISS** vector index executing normalized cosine similarity search in **< 2.1 milliseconds**.
- Evaluates queries against a **0.35 similarity floor** and injects retrieved context into an XML-bounded prompt for **Google Gemini 3.6 Flash**.
- Generates answers strictly grounded in the document with **clickable `[Page X]` citations**.

---

## 🎯 The 5 Multi-Modal Active Study Tools

| # | Modality | Route | Micro-Module | Description |
| :-: | :--- | :--- | :--- | :--- |
| **1** | **Grounded RAG Q&A** | `POST /documents/{id}/ask` | `qa.js` | Top-K FAISS vector search + grounded LLM response with verifiable `[Page X]` citations. |
| **2** | **3D Active-Recall Flashcards** | `POST /documents/{id}/flashcards` | `flashcards.js` | Interactive 3D CSS perspective card-flip deck with shuffle, single-card navigation, and grid modes. |
| **3** | **Practice Quiz Engine** | `POST /documents/{id}/quiz` | `quiz.js` | Step-by-step 4-option MCQ engine with distractor analysis, strict single-attempt locking, and instant review. |
| **4** | **1-Page Exam Cheat Sheet** | `POST /documents/{id}/summary` | `summary.js` | Condenses chapters into 4 blocks: Executive Summary, Key Takeaways, Core Definitions, and Exam Traps. |
| **5** | **Visual Concept Mind Map** | `POST /documents/{id}/mindmap` | `mindmap.js` | AI concept hierarchy compiled natively in browser as an interactive SVG flowchart via **Mermaid.js**. |

---

## 🏛️ System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                   PRESENTATION TIER (Client Browser)                   │
│  - Big Tech Royal Navy UI (HTML5 / CSS3 Responsive Theme)              │
│  - Modular ES6 Controllers (auth.js, doc.js, qa.js, quiz.js)          │
│  - Mermaid.js Client-Side SVG Flowchart Engine                         │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP REST / JWT Bearer
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│            APPLICATION TIER (FastAPI Async Engine / Docker)            │
│  - FastAPI REST Routers (/auth, /documents, /rag, /tools)              │
│  - PyMuPDF Cleaning Pipeline (>=60% noise filter + word boundary)      │
│  - Meta FAISS Vector Engine (IndexIDMap2 + FlatIP, < 2.1ms)            │
│  - Universal LLM Client (Gemini 3.6 Flash + Grounded Fallback)        │
└──────────────┬─────────────────────────────┬───────────────────────────┘
               │ SQLAlchemy Session          │ In-Memory Binary Index
               ▼                             ▼
┌──────────────────────────────┐ ┌───────────────────────────────────────┐
│ DATA TIER: MySQL / TiDB      │ │ LOCAL FILE PERSISTENCE                │
│ - users (Bcrypt 12-round)    │ │ - uploads/{user_id}/<pdf>             │
│ - documents (metadata)       │ │ - indexes/{user_id}/<doc_id>.index    │
│ - document_chunks            │ │ - Multi-tenant directory isolation    │
└──────────────────────────────┘ └───────────────────────────────────────┘
```

---

## 📊 Experimental Results & Benchmarks

Automated End-to-End (E2E) testing across **29 formal assertions** validated a **100% test pass rate**:

| Subsystem Component | Target SLA | Observed Average | Assessment |
| :--- | :---: | :---: | :--- |
| **Static Web Assets (CSS/JS)** | $< 10$ ms | **2.5 ms – 7.0 ms** | Exceptional (In-Memory HTTP Cache) |
| **PDF Extraction & Chunking** | $< 3,000$ ms | **2,056.3 ms** | Optimal (PyMuPDF C-extension throughput) |
| **FAISS Vector Search Retrieval** | $< 5$ ms | **2.1 ms** | Ultra-Fast (AVX2 SIMD Normalized Cosine) |
| **RAG Q&A Synthesis** | $< 10,000$ ms | **7,705.1 ms** | Highly Responsive (Gemini 3.6 Flash) |
| **5-Card Flashcard Deck** | $< 15,000$ ms | **10,787.1 ms** | Optimal (Structured JSON Mode) |
| **5-Question Practice Quiz** | $< 30,000$ ms | **23,604.1 ms** | Expected (Complex distractor analysis) |
| **1-Page Revision Cheat Sheet** | $< 30,000$ ms | **27,151.3 ms** | Expected (Multi-section extraction) |
| **Mermaid Concept Mind Map** | $< 30,000$ ms | **25,826.4 ms** | Expected (Hierarchical graph synthesis) |

---

## 🛠️ Technology Stack

* **Backend Framework**: Python 3.12+, FastAPI 0.110+, Uvicorn ASGI
* **Vector Search Engine**: Meta FAISS-CPU 1.8.0+ (`IndexFlatIP`, `IndexIDMap2`)
* **PDF Extraction & Ingestion**: PyMuPDF (`fitz` 1.24+), Regex
* **Embeddings & AI**: Google Gemini 3.6 Flash (`google-genai`), `sentence-transformers` (`all-MiniLM-L6-v2`)
* **Relational Database**: MySQL 8.0 / TiDB Cloud Serverless (PyMySQL, SQLAlchemy 2.0)
* **Security & Auth**: Bcrypt (12-round salt hashing), PyJWT (HS256 stateless tokens)
* **Frontend Architecture**: Vanilla JavaScript (Modular ES6+), HTML5, CSS3 Royal Theme, Mermaid.js 10.0+
* **Deployment & Containerization**: Docker, Render.com Web Service, TiDB Cloud

---

## 🚀 Local Development Setup

### 1. Clone & Set Up Environment
```bash
git clone https://github.com/davoodgouset-ux/study-with-ai.git
cd study-with-ai
python -m venv .venv

# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment (`.env`)
```env
PORT=8000
DATABASE_URL=mysql+pymysql://root:root@localhost:3306/study_with_ai
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=study_with_ai_super_secret_jwt_key_2026_prod_secure
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### 3. Run Application
```bash
uvicorn main:app --reload --port 8000
```
Open **`http://localhost:8000`** in your browser. API docs are available at **`http://localhost:8000/docs`**.

---

## 📜 License & Acknowledgements
Developed as part of the B.Tech Computer Science and Engineering curriculum at **Kalasalingam Academy of Research and Education** (2025–2026) under the guidance of **Mr. SHIRWIN PRINCE I**. Distributed under the MIT License.
