# ==============================================================================
# File: app/services/vector_service.py
# Purpose: Provider-consistent FAISS cosine-similarity indexes per document.
# ==============================================================================

import json
import os
import threading
from collections import OrderedDict
from pathlib import Path

import faiss
import numpy as np
from sqlalchemy.orm import Session

from app.models.chunk import DocumentChunk
from app.services.embedding_service import (
    EmbeddingProfile,
    EmbeddingUnavailableError,
    embed_document_batch,
    embed_query,
    profile_from_metadata,
)

INDEX_ROOT_DIR = "indexes"

# Thread-safe in-memory LRU cache for loaded FAISS indices and their profiles.
# Eliminates disk read overhead during repeated queries.
MAX_CACHED_INDEXES = 32
_index_cache: OrderedDict[tuple[int, int], tuple[faiss.Index, EmbeddingProfile]] = OrderedDict()
_index_cache_lock = threading.Lock()


def get_cached_index_and_profile(
    user_id: int, document_id: int
) -> tuple[faiss.Index | None, EmbeddingProfile | None]:
    """
    Returns (faiss_index, profile) from in-memory cache if present;
    otherwise loads from disk, caches the result, and returns it.
    """
    cache_key = (user_id, document_id)
    with _index_cache_lock:
        if cache_key in _index_cache:
            _index_cache.move_to_end(cache_key)
            return _index_cache[cache_key]

    index = load_document_index(user_id, document_id)
    profile = load_index_profile(user_id, document_id)

    if index is not None and profile is not None:
        with _index_cache_lock:
            if len(_index_cache) >= MAX_CACHED_INDEXES:
                _index_cache.popitem(last=False)
            _index_cache[cache_key] = (index, profile)
        return index, profile

    return None, None


def invalidate_index_cache(user_id: int, document_id: int) -> None:
    """Removes an index from in-memory cache upon deletion or rebuild."""
    with _index_cache_lock:
        _index_cache.pop((user_id, document_id), None)


def _get_index_dir(user_id: int) -> Path:
    path = Path(INDEX_ROOT_DIR) / str(user_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_index_path(user_id: int, document_id: int) -> str:
    return str(_get_index_dir(user_id) / f"{document_id}.faiss")


def get_index_metadata_path(user_id: int, document_id: int) -> str:
    return str(_get_index_dir(user_id) / f"{document_id}.meta.json")


def _write_index_metadata(user_id: int, document_id: int, profile: EmbeddingProfile) -> None:
    path = Path(get_index_metadata_path(user_id, document_id))
    temporary_path = path.with_suffix(".meta.json.tmp")
    temporary_path.write_text(json.dumps(profile.to_dict()), encoding="utf-8")
    os.replace(temporary_path, path)


def load_index_profile(user_id: int, document_id: int) -> EmbeddingProfile | None:
    path = Path(get_index_metadata_path(user_id, document_id))
    if not path.exists():
        return None
    try:
        return profile_from_metadata(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError, json.JSONDecodeError, EmbeddingUnavailableError):
        return None


def build_and_save_document_index(
    user_id: int,
    document_id: int,
    chunks: list[DocumentChunk],
) -> str:
    """Build an exact cosine-similarity FAISS index from one semantic provider."""
    if not chunks:
        return ""

    ordered_chunks = sorted(chunks, key=lambda chunk: chunk.chunk_index)
    texts = [chunk.chunk_text for chunk in ordered_chunks]
    embeddings, profile = embed_document_batch(texts)
    vector_matrix = np.asarray(embeddings, dtype=np.float32)
    if vector_matrix.ndim != 2 or vector_matrix.shape[1] != profile.dimension:
        raise EmbeddingUnavailableError("Embedding matrix shape does not match its profile.")

    faiss.normalize_L2(vector_matrix)
    # Store database chunk indexes as FAISS IDs, rather than relying on insertion
    # order to remain identical to a chunk's database position.
    index = faiss.IndexIDMap2(faiss.IndexFlatIP(profile.dimension))
    chunk_ids = np.asarray([chunk.chunk_index for chunk in ordered_chunks], dtype=np.int64)
    index.add_with_ids(vector_matrix, chunk_ids)

    index_path = Path(get_index_path(user_id, document_id))
    temporary_index_path = index_path.with_suffix(".faiss.tmp")
    faiss.write_index(index, str(temporary_index_path))
    os.replace(temporary_index_path, index_path)
    _write_index_metadata(user_id, document_id, profile)

    # Warm in-memory cache immediately so next search avoids disk I/O
    with _index_cache_lock:
        if len(_index_cache) >= MAX_CACHED_INDEXES:
            _index_cache.popitem(last=False)
        _index_cache[(user_id, document_id)] = (index, profile)

    return str(index_path)


def load_document_index(user_id: int, document_id: int) -> faiss.Index | None:
    path = get_index_path(user_id, document_id)
    if not os.path.exists(path):
        return None
    try:
        return faiss.read_index(path)
    except RuntimeError:
        return None


def _get_document_chunks(document_id: int, db: Session) -> list[DocumentChunk]:
    return (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document_id)
        .order_by(DocumentChunk.chunk_index.asc())
        .all()
    )


def _rebuild_index(user_id: int, document_id: int, db: Session) -> tuple[faiss.Index, EmbeddingProfile]:
    chunks = _get_document_chunks(document_id, db)
    if not chunks:
        raise EmbeddingUnavailableError("This document has no text chunks to index.")
    build_and_save_document_index(user_id, document_id, chunks)
    index, profile = get_cached_index_and_profile(user_id, document_id)
    if index is None or profile is None:
        raise EmbeddingUnavailableError("The document search index could not be rebuilt.")
    return index, profile


def search_document_chunks(
    user_id: int,
    document_id: int,
    query: str,
    db: Session,
    top_k: int = 5,
) -> list[dict]:
    """Search only vectors generated by the same model as the saved index."""
    index, profile = get_cached_index_and_profile(user_id, document_id)
    if index is None or profile is None or index.d != profile.dimension:
        index, profile = _rebuild_index(user_id, document_id, db)

    try:
        query_embedding = embed_query(query, profile)
    except EmbeddingUnavailableError:
        # Rebuild with another real semantic provider—never compare incompatible
        # local and Gemini vector spaces.
        index, profile = _rebuild_index(user_id, document_id, db)
        query_embedding = embed_query(query, profile)

    query_vector = np.asarray([query_embedding], dtype=np.float32)
    if query_vector.shape[1] != index.d:
        raise EmbeddingUnavailableError("Query and document indexes use incompatible dimensions.")
    faiss.normalize_L2(query_vector)

    k = min(top_k, index.ntotal)
    if k <= 0:
        return []
    scores, indices = index.search(query_vector, k)

    chunk_ids = [int(chunk_id) for chunk_id in indices[0] if chunk_id >= 0]
    chunk_by_index = {
        chunk.chunk_index: chunk
        for chunk in _get_document_chunks(document_id, db)
        if chunk.chunk_index in chunk_ids
    }

    results = []
    for rank, (chunk_id, score) in enumerate(zip(indices[0], scores[0]), start=1):
        chunk = chunk_by_index.get(int(chunk_id))
        if chunk is None:
            continue
        results.append({
            "rank": rank,
            "score": float(score),
            "page_number": chunk.page_number,
            "chunk_index": chunk.chunk_index,
            "chunk_text": chunk.chunk_text,
            "char_count": chunk.char_count,
        })
    return results


def delete_document_index(user_id: int, document_id: int) -> None:
    """Delete both the FAISS index and its embedding-profile metadata, and invalidate cache."""
    invalidate_index_cache(user_id, document_id)
    for path in (get_index_path(user_id, document_id), get_index_metadata_path(user_id, document_id)):
        try:
            if os.path.exists(path):
                os.remove(path)
        except OSError:
            pass
