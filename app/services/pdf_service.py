# ==============================================================================
# File: app/services/pdf_service.py
# Purpose: PDF validation, storage, and page-by-page text extraction using PyMuPDF.
# Enforces all Document Constraints (format, size, page limit, corruption checks).
# ==============================================================================

import os
import re
import unicodedata
import uuid
import pymupdf
from fastapi import HTTPException, status

# Constraints: 25 MB default upload limit (configurable via .env)
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "25"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024  # 25 MB in bytes
MAX_DOCUMENT_PAGES = 100                              # Max 100 pages per document
MAX_DOCS_PER_USER = 10                               # Max 10 documents per user
UPLOAD_DIR = "uploads"


def _normalise_page_text(text: str, repeated_margin_lines: set[str]) -> str:
    """Remove common extraction noise while keeping paragraph boundaries."""
    text = unicodedata.normalize("NFKC", text).replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.strip() for line in text.split("\n")]
    lines = [line for line in lines if line.casefold() not in repeated_margin_lines]
    text = "\n".join(lines)
    # A word split only because of a PDF line ending should become one word.
    text = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _find_repeated_margin_lines(page_texts: list[str]) -> set[str]:
    """Find likely headers/footers repeated across most pages, conservatively."""
    if len(page_texts) < 3:
        return set()

    occurrences: dict[str, int] = {}
    for page_text in page_texts:
        lines = [line.strip() for line in page_text.splitlines() if line.strip()]
        # Header/footer noise usually appears at a page margin; never inspect the
        # full page so common subject terms are not accidentally removed.
        margin_lines = lines[:2] + lines[-2:]
        for line in set(margin_lines):
            normalised = unicodedata.normalize("NFKC", line).casefold()
            if 3 <= len(normalised) <= 120 and any(char.isalpha() for char in normalised):
                occurrences[normalised] = occurrences.get(normalised, 0) + 1

    required_occurrences = max(3, int(len(page_texts) * 0.6 + 0.999))
    return {
        line for line, count in occurrences.items()
        if count >= required_occurrences
    }


def validate_pdf_metadata(filename: str, file_bytes: bytes) -> None:
    """
    Validates file extension, size, and non-empty content before heavy processing.
    """
    # Check 1: File must have .pdf extension
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format: '{filename}'. Only PDF documents are supported."
        )

    # Check 2: File must not be 0 bytes
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded PDF file is empty (0 bytes)."
        )

    # Check 3: File size must not exceed 25 MB
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        size_mb = len(file_bytes) / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size ({MAX_FILE_SIZE_MB} MB). Uploaded size: {size_mb:.2f} MB."
        )


def extract_text_from_pdf(file_bytes: bytes) -> tuple[int, list[dict], str]:
    """
    Opens the PDF in memory using PyMuPDF and extracts text page-by-page.
    
    Returns:
        tuple containing:
        - total_pages (int): Total number of pages.
        - pages_data (list[dict]): List of dicts with page_number and extracted text.
        - sample_text (str): First 300 characters of page 1 for quick visual verification.
    """
    # Step 1: Attempt to parse the PDF bytes with PyMuPDF
    try:
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Corrupted or invalid PDF file. Could not parse document: {str(e)}"
        )

    # Step 2: Check if PDF is encrypted / password-protected
    if doc.is_encrypted:
        doc.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password-protected PDFs are not supported. Please remove the password and try again."
        )

    # Step 3: Enforce page count limit (~100 pages)
    total_pages = len(doc)
    if total_pages == 0:
        doc.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded PDF contains 0 pages."
        )

    if total_pages > MAX_DOCUMENT_PAGES:
        doc.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document length exceeds limit of {MAX_DOCUMENT_PAGES} pages (document has {total_pages} pages)."
        )

    # Step 4: Extract text page-by-page while preserving page numbers
    raw_pages = []

    for page_index in range(total_pages):
        try:
            page = doc[page_index]
            # Sorting blocks gives much better reading order for ordinary PDFs.
            raw_text = page.get_text("text", sort=True).strip()
        except Exception as exc:
            doc.close()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not extract readable text from page {page_index + 1}."
            ) from exc
        raw_pages.append(raw_text)

    repeated_margin_lines = _find_repeated_margin_lines(raw_pages)
    pages_data = []
    total_chars = 0
    for page_index, raw_text in enumerate(raw_pages):
        cleaned_text = _normalise_page_text(raw_text, repeated_margin_lines)

        pages_data.append({
            "page_number": page_index + 1,  # 1-indexed for human readability
            "text": cleaned_text,
            "char_count": len(cleaned_text)
        })
        total_chars += len(cleaned_text)

    # Step 5: Check if the PDF has any readable digital text
    # (Catches scanned PDFs that are just images without an OCR text layer)
    if total_chars == 0:
        doc.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded PDF contains no readable text. Scanned image-only PDFs without OCR cannot be processed."
        )

    # Grab a preview sample from Page 1
    sample_text = pages_data[0]["text"][:300] if pages_data else ""
    doc.close()

    return total_pages, pages_data, sample_text


def save_pdf_to_disk(file_bytes: bytes, original_filename: str, user_id: int) -> str:
    """
    Saves the validated PDF safely onto disk under uploads/{user_id}/.
    Uses UUID to prevent filename collisions.
    """
    # Create user-specific uploads folder for isolation
    user_upload_dir = os.path.join(UPLOAD_DIR, str(user_id))
    os.makedirs(user_upload_dir, exist_ok=True)

    # Generate a safe unique filename: <uuid>_<clean_filename>
    safe_name = f"{uuid.uuid4().hex[:8]}_{original_filename.replace(' ', '_')}"
    target_path = os.path.join(user_upload_dir, safe_name)

    with open(target_path, "wb") as f:
        f.write(file_bytes)

    return target_path
