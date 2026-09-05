# ==============================================================================
# File: app/services/embedding_service.py
# Purpose: Generate semantic embeddings for the RAG pipeline.
#
# A retrieval system must never use random vectors as a fallback: they make FAISS
# return plausible-looking but unrelated passages. This module uses Gemini when
# available and falls back to a real local Sentence Transformer model instead.
# ==============================================================================

import os
import threading
from collections import OrderedDict
from dataclasses import asdict, dataclass
from typing import Literal

import numpy as np
from dotenv import load_dotenv
from google import genai

load_dotenv()

EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
GEMINI_EMBEDDING_DIMENSION = int(os.getenv("GEMINI_EMBEDDING_DIMENSION", "3072"))
LOCAL_EMBEDDING_MODEL = os.getenv(
    "LOCAL_EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
)
LOCAL_EMBEDDING_DEVICE = os.getenv("LOCAL_EMBEDDING_DEVICE", "cpu")

# Thread-safe in-memory LRU cache for query embeddings (avoids repeat API/model calls)
MAX_QUERY_CACHE_SIZE = 512
_query_embedding_cache: OrderedDict[tuple[str, str, int, str], list[float]] = OrderedDict()
_query_cache_lock = threading.Lock()


class EmbeddingUnavailableError(RuntimeError):
    """Raised when no configured embedding provider can create vectors."""


@dataclass(frozen=True)
class EmbeddingProfile:
    """The model identity stored beside every FAISS index."""

    provider: Literal["gemini", "local"]
    model: str
    dimension: int
    index_version: int = 2

    def to_dict(self) -> dict:
        return asdict(self)


_local_model = None


def get_genai_client() -> genai.Client | None:
    """Return a Gemini client only when a real API key is configured."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or api_key.startswith("your_") or api_key == "test_key":
        return None
    return genai.Client(api_key=api_key)


def _get_local_model():
    """Load and cache a local semantic embedding model on first use."""
    global _local_model
    if _local_model is not None:
        return _local_model

    try:
        from sentence_transformers import SentenceTransformer

        _local_model = SentenceTransformer(
            LOCAL_EMBEDDING_MODEL,
            device=LOCAL_EMBEDDING_DEVICE,
        )
        return _local_model
    except Exception as exc:
        raise EmbeddingUnavailableError(
            "Local semantic embeddings are unavailable. Install sentence-transformers "
            "and download the configured local model."
        ) from exc


def _gemini_profile() -> EmbeddingProfile | None:
    if get_genai_client() is None:
        return None
    return EmbeddingProfile("gemini", EMBEDDING_MODEL, GEMINI_EMBEDDING_DIMENSION)


def _local_profile() -> EmbeddingProfile:
    model = _get_local_model()
    return EmbeddingProfile(
        "local",
        LOCAL_EMBEDDING_MODEL,
        int(model.get_sentence_embedding_dimension()),
    )


def profile_from_metadata(metadata: dict) -> EmbeddingProfile:
    """Validate persisted index metadata before using it."""
    try:
        provider = metadata["provider"]
        if provider not in {"gemini", "local"}:
            raise ValueError("unknown provider")
        return EmbeddingProfile(
            provider=provider,
            model=str(metadata["model"]),
            dimension=int(metadata["dimension"]),
            index_version=int(metadata.get("index_version", 1)),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise EmbeddingUnavailableError("Saved embedding-index metadata is invalid.") from exc


def _embed_with_gemini(texts: list[str], task_type: str) -> list[list[float]]:
    client = get_genai_client()
    if client is None:
        raise EmbeddingUnavailableError("Gemini embedding credentials are not configured.")

    vectors: list[list[float]] = []
    batch_size = 10
    try:
        for start in range(0, len(texts), batch_size):
            batch = texts[start:start + batch_size]
            response = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=batch,
                config={"task_type": task_type},
            )
            batch_vectors = [embedding.values for embedding in response.embeddings or []]
            if len(batch_vectors) != len(batch):
                raise ValueError("Gemini returned an incomplete embedding batch.")
            vectors.extend(batch_vectors)
    except Exception as exc:
        raise EmbeddingUnavailableError("Gemini could not create embeddings.") from exc
    return vectors


def _embed_with_local(texts: list[str], task_type: str) -> list[list[float]]:
    model = _get_local_model()
    try:
        # Models with retrieval prompts use them; older models use encode().
        if task_type == "RETRIEVAL_QUERY" and hasattr(model, "encode_query"):
            vectors = model.encode_query(texts, normalize_embeddings=True)
        elif task_type == "RETRIEVAL_DOCUMENT" and hasattr(model, "encode_document"):
            vectors = model.encode_document(texts, normalize_embeddings=True)
        else:
            vectors = model.encode(texts, normalize_embeddings=True)
        return np.asarray(vectors, dtype=np.float32).tolist()
    except Exception as exc:
        raise EmbeddingUnavailableError("The local semantic embedding model failed.") from exc


def embed_texts(
    texts: list[str],
    profile: EmbeddingProfile,
    task_type: str,
) -> list[list[float]]:
    """Embed a complete batch with exactly one provider—never mix vector spaces."""
    if not texts:
        return []
    if profile.provider == "gemini":
        if profile.model != EMBEDDING_MODEL:
            raise EmbeddingUnavailableError("The saved Gemini index uses a different embedding model.")
        vectors = _embed_with_gemini(texts, task_type)
    elif profile.provider == "local":
        if profile.model != LOCAL_EMBEDDING_MODEL:
            raise EmbeddingUnavailableError("The saved local index uses a different embedding model.")
        vectors = _embed_with_local(texts, task_type)
    else:
        raise EmbeddingUnavailableError("Unsupported embedding provider.")

    if any(len(vector) != profile.dimension for vector in vectors):
        raise EmbeddingUnavailableError(
            "The embedding provider returned vectors with an unexpected dimension."
        )
    return vectors


def _embed_with_available_provider(
    texts: list[str], task_type: str
) -> tuple[list[list[float]], EmbeddingProfile]:
    """Embed a complete batch with the first fully available semantic provider."""
    errors = []
    # Do not load/download the local model while Gemini is healthy. The local
    # model is deliberately lazy and is only started after Gemini fails.
    gemini_profile = _gemini_profile()
    if gemini_profile:
        try:
            return embed_texts(texts, gemini_profile, task_type), gemini_profile
        except EmbeddingUnavailableError as exc:
            errors.append(str(exc))

    try:
        local_profile = _local_profile()
        return embed_texts(texts, local_profile, task_type), local_profile
    except EmbeddingUnavailableError as exc:
        errors.append(str(exc))

    detail = " ".join(errors) or "No embedding provider is configured."
    raise EmbeddingUnavailableError(detail)


def embed_document_batch(texts: list[str]) -> tuple[list[list[float]], EmbeddingProfile]:
    """Embed a document with the first fully available semantic provider."""
    return _embed_with_available_provider(texts, "RETRIEVAL_DOCUMENT")


def embed_query(text: str, profile: EmbeddingProfile) -> list[float]:
    """Embed a query in the exact vector space used by its FAISS index with LRU caching."""
    clean_text = text.strip().lower()
    cache_key = (profile.provider, profile.model, profile.dimension, clean_text)

    with _query_cache_lock:
        if cache_key in _query_embedding_cache:
            _query_embedding_cache.move_to_end(cache_key)
            return _query_embedding_cache[cache_key]

    vector = embed_texts([text], profile, "RETRIEVAL_QUERY")[0]

    with _query_cache_lock:
        if len(_query_embedding_cache) >= MAX_QUERY_CACHE_SIZE:
            _query_embedding_cache.popitem(last=False)
        _query_embedding_cache[cache_key] = vector

    return vector


# Compatibility helpers for the existing learning/demo scripts. Application code
# should use profile-aware functions above so document and query vectors match.
def get_text_embedding(text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
    vectors, _ = _embed_with_available_provider([text], task_type)
    return vectors[0]


def get_batch_embeddings(
    texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT"
) -> list[list[float]]:
    vectors, _ = _embed_with_available_provider(texts, task_type)
    return vectors
