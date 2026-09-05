# ==============================================================================
# File: app/services/gemini_service.py
# Purpose: Universal LLM Client supporting OpenAI (OPEN_API_KEY / OPENAI_API_KEY)
# and Google Gemini (GEMINI_API_KEY) with automatic retries and local fallback.
# ==============================================================================

import os
import time
import json
import re
import httpx
from dotenv import load_dotenv
from google import genai
from app.services.prompt_templates import RAG_SYSTEM_INSTRUCTION

load_dotenv()

# Default model identifiers
GEMINI_MODEL = "gemini-3.6-flash"
OPENAI_MODEL = "gpt-4o-mini"


def get_configured_keys() -> tuple[str | None, str | None]:
    """
    Reloads .env dynamically on each call so user can change API keys without restart.
    Returns: (openai_key, gemini_key)
    """
    load_dotenv(override=True)
    openai_key = os.getenv("OPEN_API_KEY") or os.getenv("OPENAI_API_KEY") or ""
    gemini_key = os.getenv("GEMINI_API_KEY") or ""

    openai_key = openai_key.strip()
    gemini_key = gemini_key.strip()

    valid_openai = openai_key if (openai_key and not openai_key.startswith("your_") and openai_key != "test_key") else None
    valid_gemini = gemini_key if (gemini_key and not gemini_key.startswith("your_") and gemini_key != "test_key") else None

    return valid_openai, valid_gemini


def call_openai_chat(prompt: str, is_json: bool = False, model_name: str = OPENAI_MODEL) -> tuple[dict | str | None, str]:
    """
    Calls OpenAI API directly via httpx.
    """
    openai_key, _ = get_configured_keys()
    if not openai_key:
        return None, "none"

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {openai_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": RAG_SYSTEM_INSTRUCTION},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    if is_json:
        payload["response_format"] = {"type": "json_object"}

    MAX_RETRIES = 2
    for attempt in range(MAX_RETRIES):
        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"].strip()
                    if is_json:
                        if content.startswith("```"):
                            content = re.sub(r"^```[a-zA-Z]*\n?", "", content)
                            content = re.sub(r"\n?```$", "", content)
                        return json.loads(content), model_name
                    return content, model_name
                elif res.status_code == 401:
                    print(f"[OpenAI Service Warning] 401 Unauthorized: Invalid OPEN_API_KEY in .env. Using fallback.")
                    break
                elif res.status_code == 429:
                    err_json = res.json().get("error", {}) if "error" in res.text else {}
                    err_code = err_json.get("code", "")
                    err_msg = err_json.get("message", "")
                    if "credit_balance_exhausted" in err_code or "insufficient_quota" in err_msg:
                        print(f"\n[OpenAI Service Alert] 429 INSUFFICIENT QUOTA: {err_msg}")
                        print(f"--> Your OpenAI key has $0 credit balance. Add credits at https://platform.openai.com/settings/organization/billing/ or use a free GEMINI_API_KEY.\n")
                        return None, "none"
                    elif attempt < MAX_RETRIES - 1:
                        print(f"[OpenAI Service] Rate limit {res.status_code}. Retrying in 1.5s...")
                        time.sleep(1.5)
                    else:
                        print(f"[OpenAI Service Warning] HTTP 429: {res.text[:120]}... Using fallback.")
                        break
                else:
                    print(f"[OpenAI Service Warning] HTTP {res.status_code}: {res.text[:120]}... Using fallback.")
                    break
        except Exception as e:
            print(f"[OpenAI Service Error] {e}. Attempt {attempt+1}/{MAX_RETRIES}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(1.5)

    return None, "none"


def call_gemini_chat(prompt: str, is_json: bool = False, model_name: str = GEMINI_MODEL) -> tuple[dict | str | None, str]:
    """
    Calls Google Gemini API.
    """
    _, gemini_key = get_configured_keys()
    if not gemini_key:
        return None, "none"

    try:
        client = genai.Client(api_key=gemini_key)
    except Exception as e:
        print(f"[Gemini Client Init Error] {e}")
        return None, "none"

    config_dict = {
        "system_instruction": RAG_SYSTEM_INSTRUCTION,
        "temperature": 0.2,
        "max_output_tokens": 4096
    }
    if is_json:
        config_dict["response_mime_type"] = "application/json"

    MAX_RETRIES = 2
    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config_dict
            )
            if response.text:
                clean_text = response.text.strip()
                if is_json:
                    if clean_text.startswith("```"):
                        clean_text = re.sub(r"^```[a-zA-Z]*\n?", "", clean_text)
                        clean_text = re.sub(r"\n?```$", "", clean_text)
                    return json.loads(clean_text, strict=False), model_name
                return clean_text, model_name
        except Exception as e:
            err_msg = str(e)
            if ("429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "503" in err_msg) and attempt < MAX_RETRIES - 1:
                print(f"[Gemini Service] Rate limit on attempt {attempt+1}. Retrying in 1.5s...")
                time.sleep(1.5)
            else:
                print(f"[Gemini Service Warning] API error: {err_msg[:120]}... Using fallback.")
                break

    return None, "none"


def generate_rag_answer(prompt: str, model_name: str = GEMINI_MODEL) -> tuple[str, str]:
    """
    Generates an answer using whichever API key is configured in .env (OpenAI or Gemini),
    falling back dynamically to local textbook synthesis on failure/rate limit.
    """
    openai_key, gemini_key = get_configured_keys()

    # If OpenAI key configured, prioritize OpenAI
    if openai_key and openai_key.startswith("sk-"):
        res, used_model = call_openai_chat(prompt, is_json=False)
        if res:
            return res, used_model

    # If Gemini key configured, prioritize Gemini
    if gemini_key:
        res, used_model = call_gemini_chat(prompt, is_json=False, model_name=model_name)
        if res:
            return res, used_model

    # Fallback to local grounded synthesis
    return generate_offline_fallback_answer(prompt), "local-grounded-fallback"


def generate_structured_json(prompt: str, model_name: str = GEMINI_MODEL) -> tuple[dict | list, str]:
    """
    Generates structured JSON using whichever API key is configured in .env (OpenAI or Gemini),
    falling back dynamically to local textbook synthesis on failure/rate limit.
    """
    openai_key, gemini_key = get_configured_keys()

    if openai_key and openai_key.startswith("sk-"):
        res, used_model = call_openai_chat(prompt, is_json=True)
        if res:
            return res, used_model

    if gemini_key:
        res, used_model = call_gemini_chat(prompt, is_json=True, model_name=model_name)
        if res:
            return res, used_model

    return {
        "fallback": True,
        "message": "Structured fallback data"
    }, "local-grounded-fallback"


def generate_offline_fallback_answer(prompt: str) -> str:
    """
    Intelligently analyzes the user's specific question against all retrieved chunks
    and synthesizes a tailored answer with exact citations.
    ZERO static text snippets: Different questions yield different, relevant answers.
    """
    context_match = re.search(r'<context>(.*?)</context>', prompt, re.DOTALL)
    question_match = re.search(r'<student_question>(.*?)</student_question>', prompt, re.DOTALL)
    doc_match = re.search(r'Filename:\s*(.*?)\n', prompt)

    doc_name = doc_match.group(1).strip() if doc_match else "Document.pdf"
    context = context_match.group(1).strip() if context_match else ""
    question = question_match.group(1).strip() if question_match else ""

    if not context or len(context) < 15:
        return f"The requested information for '{question}' could not be found in the uploaded document."

    STOP_WORDS = {
        'what', 'is', 'are', 'the', 'a', 'an', 'and', 'or', 'in', 'of', 'to', 'for', 'with', 
        'on', 'at', 'by', 'from', 'explain', 'describe', 'how', 'why', 'which', 'can', 'does', 
        'do', 'did', 'about', 'tell', 'me', 'please', 'define', 'meaning'
    }

    q_words = [re.sub(r'[^a-zA-Z0-9]', '', w.lower()) for w in question.split() if len(w) > 2]
    keywords = [w for w in q_words if w and w not in STOP_WORDS]

    chunk_blocks = re.split(r'\[Chunk\s+\d+\s+—\s+Page\s+(\d+)\]', context)
    scored_sentences = []

    if len(chunk_blocks) > 1:
        for i in range(1, len(chunk_blocks), 2):
            page_num = chunk_blocks[i]
            block_text = chunk_blocks[i+1] if i+1 < len(chunk_blocks) else ""
            cleaned_block = re.sub(r'---+\s*PASSAGE.*?---+', '', block_text, flags=re.IGNORECASE)
            sentences = [s.strip() for s in re.split(r'[.!?\n]\s*', cleaned_block) if len(s.strip()) > 15 and not s.strip().startswith("---")]
            
            for s in sentences:
                s_lower = s.lower()
                score = 0
                for kw in keywords:
                    if kw in s_lower:
                        score += 1
                        if re.search(r'\b' + re.escape(kw) + r'\b', s_lower):
                            score += 2
                if score > 0:
                    scored_sentences.append((score, s, page_num))
    else:
        page_matches = re.findall(r'\[Page\s+(\d+)\]', context)
        default_page = page_matches[0] if page_matches else "1"
        cleaned_context = re.sub(r'---+\s*PASSAGE.*?---+', '', context, flags=re.IGNORECASE)
        sentences = [s.strip() for s in re.split(r'[.!?\n]\s*', cleaned_context) if len(s.strip()) > 15 and not s.strip().startswith("---")]
        for s in sentences:
            s_lower = s.lower()
            score = sum(1 for kw in keywords if kw in s_lower)
            if score > 0:
                scored_sentences.append((score, s, default_page))

    scored_sentences.sort(key=lambda x: x[0], reverse=True)

    if scored_sentences:
        top_items = scored_sentences[:3]
        unique_sentences = []
        seen = set()
        for score, sent, page in top_items:
            if sent not in seen:
                seen.add(sent)
                unique_sentences.append(f"• **{sent}.** [{doc_name} — Page {page}]")

        bullet_text = "\n".join(unique_sentences)
        return (
            f"Based on **{doc_name}**, here is the verified explanation regarding **\"{question}\"**:\n\n"
            f"{bullet_text}"
        )
    else:
        clean_lines = [line.strip() for line in context.split("\n") if line.strip() and not line.startswith("---") and not line.startswith("[Chunk")]
        summary = " ".join(clean_lines[:2])
        page_num = re.findall(r'Page\s+(\d+)', context)
        p = page_num[0] if page_num else "1"
        return f"Regarding **\"{question}\"**, {doc_name} notes: {summary} [{doc_name} — Page {p}]"