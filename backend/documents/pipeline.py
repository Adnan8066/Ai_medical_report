"""
End-to-end document pipeline: OCR -> extracted text -> RAG index -> AI summary.

The pipeline is synchronous so a demo upload immediately shows every stage of
the workflow; each stage records its own status so it can be moved to a task
queue (Celery/RQ) without changing the API contract.
"""

import logging

from .models import AISummary, ExtractedText, MedicalDocument
from .services import ai, ocr, rag

logger = logging.getLogger(__name__)


def process_document(document, run_ai=True):
    """Run the full pipeline for ``document`` and return a status summary."""
    document.ocr_status = MedicalDocument.OCRStatus.PROCESSING
    document.ocr_error = ""
    document.save(update_fields=["ocr_status", "ocr_error", "updated_at"])

    result = ocr.extract_text(document.file)
    text = result.get("text") or ""

    ExtractedText.objects.update_or_create(
        document=document,
        defaults={
            "text": text,
            "language": "eng",
            "engine": result.get("engine", "unknown"),
            "confidence": result.get("confidence"),
            "page_count": result.get("pages") or 1,
            "char_count": len(text),
            "preprocessing_notes": (result.get("notes") or "")[:250],
        },
    )

    chunks_indexed = rag.index_document(document, text) if text else 0

    summary_payload = None
    if run_ai:
        summary_payload = ai.summarise_document(
            text, category_hint=document.get_category_display()
        )
        AISummary.objects.update_or_create(
            document=document,
            defaults={
                "summary": summary_payload["summary"],
                "key_points": summary_payload["key_points"],
                "medications": summary_payload["medications"],
                "lab_values": summary_payload["lab_values"],
                "important_dates": summary_payload["important_dates"],
                "classification": summary_payload["classification"],
                "provider": summary_payload["provider"],
                "model_name": (
                    ai.settings.OPENAI_MODEL
                    if summary_payload["provider"] == "openai"
                    else "local-extractive"
                ),
                "confidence": result.get("confidence"),
            },
        )

    if text:
        document.ocr_status = MedicalDocument.OCRStatus.COMPLETED
        document.ocr_error = ""
    else:
        document.ocr_status = MedicalDocument.OCRStatus.FAILED
        document.ocr_error = (result.get("notes") or "No text could be extracted.")[:250]
    document.save(update_fields=["ocr_status", "ocr_error", "updated_at"])

    return {
        "document": document,
        "engine": result.get("engine"),
        "char_count": len(text),
        "chunks_indexed": chunks_indexed,
        "summary": summary_payload,
        "ocr_status": document.ocr_status,
        "message": (
            "Text extracted successfully."
            if text
            else document.ocr_error or "No text could be extracted from this file."
        ),
    }
