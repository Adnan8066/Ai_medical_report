"""
OCR pipeline: preprocess -> recognise -> clean up.

The pipeline uses OpenCV for image preprocessing and Tesseract (via
``pytesseract``) for recognition.  When Tesseract is not installed on the host
the module degrades gracefully:

* PDFs are still read with ``pypdf`` (embedded text layer).
* Images return a clearly labelled demo fallback so the platform stays usable
  and the UI can explain that no real text was extracted.
"""

import logging
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)

TESSERACT_HINT = (
    "Tesseract OCR was not available on this machine, so no text could be read "
    "from the image. Install Tesseract and set TESSERACT_CMD in your .env file "
    "to enable full OCR."
)


def _configure_tesseract():
    try:
        import pytesseract
    except ImportError:  # pragma: no cover - optional dependency
        return None
    if settings.TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
    return pytesseract


def tesseract_available():
    """Return True when the Tesseract binary can be reached."""
    pytesseract = _configure_tesseract()
    if pytesseract is None:
        return False
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def preprocess_image(path):
    """
    Improve contrast and remove noise before recognition.

    Returns ``(image_array, note)``.  When OpenCV is unavailable the original
    image is returned untouched.
    """
    try:
        import cv2
        import numpy as np
    except ImportError:  # pragma: no cover - optional dependency
        return None, "OpenCV not installed - pre-processing skipped."

    image = cv2.imread(str(path))
    if image is None:
        return None, "Image could not be read by OpenCV."

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    gray = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        15,
    )
    gray = cv2.medianBlur(gray, 3)
    return gray, "Grayscale + adaptive threshold + median blur applied."


def extract_from_image(path):
    """Run OCR on an image file."""
    notes = []
    array, note = preprocess_image(path)
    notes.append(note)

    pytesseract = _configure_tesseract()
    if pytesseract is None:
        notes.append("pytesseract is not installed.")
        return {"text": "", "confidence": None, "engine": "unavailable", "notes": " ".join(notes)}

    if not tesseract_available():
        notes.append(TESSERACT_HINT)
        return {
            "text": "",
            "confidence": None,
            "engine": "tesseract-missing",
            "notes": " ".join(filter(None, notes)),
        }

    try:
        if array is not None:
            text = pytesseract.image_to_string(array)
        else:
            text = pytesseract.image_to_string(str(path))
        data = pytesseract.image_to_data(
            array if array is not None else str(path), output_type=pytesseract.Output.DICT
        )
        confidences = [
            float(value)
            for value in data.get("conf", [])
            if str(value).strip() not in {"", "-1"}
        ]
        confidence = sum(confidences) / len(confidences) / 100 if confidences else None
        notes.append("Tesseract OCR completed.")
        return {
            "text": text.strip(),
            "confidence": confidence,
            "engine": "tesseract",
            "notes": " ".join(filter(None, notes)),
        }
    except Exception as exc:  # pragma: no cover - depends on host install
        logger.warning("OCR failed for %s: %s", path, exc)
        notes.append(f"OCR error: {exc}")
        return {
            "text": "",
            "confidence": None,
            "engine": "tesseract-error",
            "notes": " ".join(filter(None, notes)),
        }


def extract_from_pdf(path):
    """Read embedded text from a PDF, page by page."""
    try:
        from pypdf import PdfReader
    except ImportError:  # pragma: no cover - optional dependency
        return {
            "text": "",
            "confidence": None,
            "engine": "pypdf-missing",
            "notes": "pypdf is not installed, so the PDF text layer could not be read.",
            "pages": 0,
        }

    try:
        reader = PdfReader(str(path))
        pages = []
        for index, page in enumerate(reader.pages[: settings.OCR_MAX_PDF_PAGES]):
            try:
                pages.append(page.extract_text() or "")
            except Exception as exc:  # pragma: no cover - defensive
                pages.append("")
                logger.warning("Failed to read page %s of %s: %s", index, path, exc)
        text = "\n".join(pages).strip()
        notes = [f"Read {len(reader.pages)} page(s) with pypdf."]
        if not text:
            notes.append(
                "This PDF has no embedded text layer (likely a scan). "
                "Install Tesseract to OCR scanned documents."
            )
        return {
            "text": text,
            "confidence": 0.99 if text else None,
            "engine": "pypdf",
            "notes": " ".join(notes),
            "pages": len(reader.pages),
        }
    except Exception as exc:
        logger.warning("PDF extraction failed for %s: %s", path, exc)
        return {
            "text": "",
            "confidence": None,
            "engine": "pypdf-error",
            "notes": f"PDF could not be read: {exc}",
            "pages": 0,
        }


def extract_text(file_field):
    """
    Dispatch on file type and always return a result dictionary.

    Keys: ``text``, ``confidence``, ``engine``, ``notes``, ``pages``.
    """
    if not file_field:
        return {
            "text": "",
            "confidence": None,
            "engine": "none",
            "notes": "No file attached.",
            "pages": 0,
        }

    path = Path(file_field.path)
    suffix = path.suffix.lower().lstrip(".")

    if suffix == "pdf":
        result = extract_from_pdf(path)
    elif suffix in {"png", "jpg", "jpeg"}:
        result = extract_from_image(path)
    else:
        result = {
            "text": "",
            "confidence": None,
            "engine": "unsupported",
            "notes": f"Unsupported file type '.{suffix}'.",
        }
    result.setdefault("pages", 1)
    result["char_count"] = len(result.get("text") or "")
    return result


def ocr_status():
    """Health information for the OCR settings panel."""
    available = tesseract_available()
    return {
        "enabled": settings.ENABLE_OCR,
        "tesseract_available": available,
        "engine": "tesseract" if available else "fallback",
        "pdf_reader": "pypdf",
        "image_preprocessing": "opencv",
        "message": (
            "Tesseract OCR detected - full text extraction enabled."
            if available
            else TESSERACT_HINT
        ),
    }
