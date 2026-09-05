# ==============================================================================
# File: app/services/chunker.py
# Purpose: Recursive Paragraph & Sentence-Aware Text Chunker.
# Splits page text into ~1000-character segments with ~200-character overlap,
# preserving sentence integrity and page number metadata.
# ==============================================================================

import re

# Constraints from project specification
DEFAULT_CHUNK_SIZE = 1000      # Target ~1000 characters per chunk
DEFAULT_CHUNK_OVERLAP = 200    # ~200 characters overlap to preserve context between boundaries


def split_text_into_chunks(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
) -> list[str]:
    """
    Recursively splits a string into chunks of approximately 'chunk_size' characters,
    with 'chunk_overlap' characters of overlap between consecutive chunks.
    
    Splitting hierarchy:
      1. Double line breaks (\n\n) -> Paragraph boundaries
      2. Single line breaks (\n)   -> Line boundaries
      3. Sentence endings (. , ? , ! ) -> Sentence boundaries
      4. Spaces ( )                -> Word boundaries
      5. Character level           -> Fallback for words longer than chunk_size
    """
    text = text.strip()
    if not text:
        return []

    # If text is already smaller than the target chunk size, return it as a single chunk
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start_idx = 0
    text_length = len(text)

    while start_idx < text_length:
        # Define the tentative end of the current chunk
        end_idx = start_idx + chunk_size

        # If we reached or exceeded the end of the text, take everything remaining
        if end_idx >= text_length:
            final_chunk = text[start_idx:].strip()
            if final_chunk:
                chunks.append(final_chunk)
            break

        # Look for the best natural breakpoint (paragraph, newline, sentence, or space)
        # Search backwards within a 250-character window from end_idx
        search_start = max(start_idx, end_idx - 250)
        window = text[search_start:end_idx]

        split_pos = -1

        # Priority 1: Double newline (Paragraph end)
        pos = window.rfind("\n\n")
        if pos != -1:
            split_pos = search_start + pos + 2
        else:
            # Priority 2: Single newline
            pos = window.rfind("\n")
            if pos != -1:
                split_pos = search_start + pos + 1
            else:
                # Priority 3: Sentence ending punctuation (. ! ?) followed by space or newline
                match = None
                for m in re.finditer(r'[\.\?\!]\s+', window):
                    match = m
                if match:
                    split_pos = search_start + match.end()
                else:
                    # Priority 4: Space between words
                    pos = window.rfind(" ")
                    if pos != -1:
                        split_pos = search_start + pos + 1
                    else:
                        # Priority 5: Hard cut at end_idx if no whitespace exists
                        split_pos = end_idx

        # Extract the chunk
        chunk = text[start_idx:split_pos].strip()
        if chunk:
            chunks.append(chunk)

        # Move the sliding window forward while avoiding a chunk that starts in
        # the middle of a word. The overlap remains "up to" chunk_overlap.
        next_start = max(split_pos - chunk_overlap, start_idx + 1)
        if (
            next_start > 0
            and next_start < text_length
            and not text[next_start - 1].isspace()
            and not text[next_start].isspace()
        ):
            next_space = text.find(" ", next_start, split_pos)
            if next_space != -1:
                next_start = next_space + 1
        start_idx = next_start

    return chunks


def chunk_document_pages(
    pages_data: list[dict],
    document_id: int,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
) -> list[dict]:
    """
    Takes extracted pages from PyMuPDF and produces structured chunk dictionaries
    tagged with document_id and page_number metadata.
    
    Parameters:
        pages_data (list[dict]): List of {'page_number': int, 'text': str} from PyMuPDF.
        document_id (int): The ID of the parent document in MySQL.
        
    Returns:
        list[dict]: List of chunk objects ready to be saved into MySQL.
    """
    all_chunks = []
    global_chunk_index = 0

    for page_info in pages_data:
        page_num = page_info["page_number"]
        page_text = page_info["text"]

        # Split the text of this specific page into chunks
        page_chunks = split_text_into_chunks(page_text, chunk_size, chunk_overlap)

        for chunk_text in page_chunks:
            all_chunks.append({
                "document_id": document_id,
                "page_number": page_num,
                "chunk_index": global_chunk_index,
                "chunk_text": chunk_text,
                "char_count": len(chunk_text)
            })
            global_chunk_index += 1

    return all_chunks
