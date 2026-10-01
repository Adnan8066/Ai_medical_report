"""
Retrieval-Augmented Generation pipeline.

Medical document -> text extraction -> chunking -> embeddings -> vector store
-> similarity search -> answer with source references.

The embedding model is a deterministic local hashing vectoriser, which keeps the
demo self-contained (no external vector service, no API key) while still giving
genuine semantic-ish retrieval over the document corpus.  The interface is the
one a hosted embedding model would use, so swapping it later is a one-file
change.
"""

import hashlib
import math
import re
from collections import Counter

from django.conf import settings

from ..models import DocumentChunk, MedicalDocument

TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9\-]{1,}")


def tokenise(text):
    return TOKEN_PATTERN.findall((text or "").lower())


def chunk_text(text, size=None, overlap=None):
    """Split text into overlapping word windows."""
    size = size or settings.RAG_CHUNK_SIZE
    overlap = overlap if overlap is not None else settings.RAG_CHUNK_OVERLAP
    words = (text or "").split()
    if not words:
        return []
    step = max(1, size - overlap)
    chunks = []
    for start in range(0, len(words), step):
        window = words[start : start + size]
        if not window:
            break
        chunks.append(" ".join(window))
        if start + size >= len(words):
            break
    return chunks


def embed(text):
    """
    Deterministic hashed bag-of-words embedding with sub-linear term weighting.

    The vector is L2 normalised so cosine similarity is a plain dot product.
    """
    dimensions = settings.EMBEDDING_DIMENSIONS
    vector = [0.0] * dimensions
    tokens = tokenise(text)
    if not tokens:
        return vector

    counts = Counter(tokens)
    for token, count in counts.items():
        weight = 1.0 + math.log(count)
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        primary = int.from_bytes(digest[:4], "big") % dimensions
        secondary = int.from_bytes(digest[4:8], "big") % dimensions
        sign = -1.0 if digest[8] % 2 else 1.0
        vector[primary] += weight
        vector[secondary] += sign * weight * 0.5

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def cosine_similarity(left, right):
    if not left or not right:
        return 0.0
    return sum(a * b for a, b in zip(left, right))


def index_document(document, text):
    """(Re)build the vector store entries for a document."""
    DocumentChunk.objects.filter(document=document).delete()
    chunks = chunk_text(text)
    created = []
    for index, chunk in enumerate(chunks):
        created.append(
            DocumentChunk(
                document=document,
                chunk_index=index,
                text=chunk,
                embedding=embed(chunk),
                source_label=f"{document.title} - part {index + 1}",
                token_estimate=len(chunk.split()),
            )
        )
    if created:
        DocumentChunk.objects.bulk_create(created)
    return len(created)


def search(query, documents_queryset, top_k=None):
    """
    Return the most relevant chunks for ``query``.

    ``documents_queryset`` must already be authorised for the caller - the RAG
    layer never widens access beyond the documents it is given.
    """
    top_k = top_k or settings.RAG_TOP_K
    query_vector = embed(query)
    if not any(query_vector):
        return []

    chunks = DocumentChunk.objects.filter(document__in=documents_queryset).select_related(
        "document"
    )
    scored = []
    for chunk in chunks:
        score = cosine_similarity(query_vector, chunk.embedding or [])
        if score > 0:
            scored.append((score, chunk))
    scored.sort(key=lambda row: row[0], reverse=True)

    results = []
    for score, chunk in scored[:top_k]:
        results.append(
            {
                "document_id": chunk.document_id,
                "document_code": chunk.document.document_id,
                "title": chunk.document.title,
                "category": chunk.document.get_category_display(),
                "chunk_index": chunk.chunk_index,
                "score": round(score, 4),
                "snippet": _highlight(chunk.text, query),
                "source": chunk.source_label
                or f"{chunk.document.title} - part {chunk.chunk_index + 1}",
            }
        )
    return results


def _highlight(text, query, window=300):
    """Trim a chunk down to the most query-relevant window."""
    terms = set(tokenise(query))
    words = text.split()
    if not terms or len(words) <= 60:
        return text[:window] + ("..." if len(text) > window else "")

    best_index, best_score = 0, -1
    for start in range(0, max(1, len(words) - 40), 15):
        window_words = words[start : start + 60]
        score = sum(1 for word in window_words if word.lower() in terms)
        if score > best_score:
            best_index, best_score = start, score

    snippet = " ".join(words[best_index : best_index + 60])
    prefix = "..." if best_index > 0 else ""
    suffix = "..." if best_index + 60 < len(words) else ""
    return f"{prefix}{snippet}{suffix}"


def build_answer(query, results, patient_name=""):
    """Compose a grounded answer strictly from the retrieved chunks."""
    if not results:
        return (
            "No matching content was found in the documents you are authorised to "
            "view. No information has been invented or inferred.",
            [],
        )

    lines = []
    if patient_name:
        lines.append(f"According to the uploaded documents for {patient_name}:")
    else:
        lines.append("According to the uploaded documents:")

    for item in results:
        lines.append(f"- {item['title']} ({item['category']}): {item['snippet']}")

    lines.append(
        "The information above is quoted or paraphrased directly from the listed "
        "documents. Nothing has been added that does not appear in the source text."
    )
    return "\n".join(lines), results


def store_summary_chunks(document, summary_text):
    """Index the generated summary so the assistant can cite it too."""
    return index_document(document, summary_text)
