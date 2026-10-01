"""
AI layer for medical documents.

Scope and safety
----------------
The assistant is deliberately restricted to *organising, summarising and
retrieving* information that already exists inside an uploaded document.  It
never diagnoses, never prescribes, never recommends treatment and never makes
an autonomous clinical decision.  Every response carries the disclaimer below
and is presented as decision *support* for an authorised healthcare
professional.

Two providers are supported:

* ``openai`` - used when ``OPENAI_API_KEY`` is configured.
* ``demo``   - a deterministic, fully local extractive engine (default) so the
  platform is always demonstrable without any external service or API key.
"""

import json
import logging
import re
import urllib.error
import urllib.request
from collections import Counter

from django.conf import settings

logger = logging.getLogger(__name__)

AI_DISCLAIMER = (
    "AI-generated information is for administrative and information-support "
    "purposes only and must be reviewed by an authorized healthcare professional."
)

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "were", "was", "are",
    "has", "have", "had", "not", "but", "his", "her", "she", "him", "they",
    "their", "patient", "patients", "will", "shall", "been", "which", "who",
    "also", "than", "then", "into", "over", "after", "before", "under", "more",
    "most", "some", "such", "any", "all", "can", "may", "should", "would",
    "could", "there", "these", "those", "when", "while", "about", "above",
    "below", "between", "during", "each", "other", "only", "same", "very",
}

MEDICATION_PREFIXES = (
    "tab", "tablet", "cap", "capsule", "inj", "injection", "syrup", "syp",
    "susp", "ointment", "cream", "drops", "inhaler", "iv", "im", "spray",
    "gel", "powder", "sachet",
)

KNOWN_MEDICATIONS = (
    "paracetamol", "acetaminophen", "ibuprofen", "aspirin", "amoxicillin",
    "azithromycin", "ceftriaxone", "cefuroxime", "metformin", "glimepiride",
    "insulin", "atorvastatin", "rosuvastatin", "amlodipine", "telmisartan",
    "losartan", "ramipril", "enalapril", "metoprolol", "bisoprolol",
    "furosemide", "spironolactone", "pantoprazole", "omeprazole", "ranitidine",
    "ondansetron", "domperidone", "levothyroxine", "prednisolone",
    "dexamethasone", "salbutamol", "montelukast", "cetirizine", "levocetirizine",
    "warfarin", "clopidogrel", "heparin", "enoxaparin", "tramadol",
    "diclofenac", "naproxen", "cefixime", "doxycycline", "metronidazole",
    "fluconazole", "acyclovir", "vitamin", "calcium", "ferrous", "iron",
    "folic", "cyanocobalamin", "ors", "saline", "dextrose", "rituximab",
    "carboplatin", "cisplatin", "paclitaxel", "tamoxifen", "levetiracetam",
    "phenytoin", "valproate", "carbamazepine", "amitriptyline", "sertraline",
    "escitalopram", "clonazepam", "alprazolam", "quetiapine", "risperidone",
)

LAB_ANALYTES = (
    "hemoglobin", "haemoglobin", "hb", "wbc", "rbc", "platelet", "platelets",
    "esr", "crp", "glucose", "fasting glucose", "postprandial glucose",
    "hba1c", "creatinine", "urea", "sodium", "potassium", "chloride",
    "calcium", "cholesterol", "triglycerides", "hdl", "ldl", "vldl",
    "tsh", "t3", "t4", "bilirubin", "sgpt", "sgot", "alt", "ast", "alp",
    "albumin", "protein", "uric acid", "amylase", "lipase", "cpk", "troponin",
    "d-dimer", "inr", "pt", "aptt", "ph", "specific gravity", "vitamin d",
    "vitamin b12", "psa", "ferritin", "iron", "tlc", "dlc", "mcv", "mch",
)

DATE_PATTERNS = (
    r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
    r"\b\d{4}-\d{2}-\d{2}\b",
    r"\b\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{2,4}\b",
    r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+\d{2,4}\b",
)

CLASSIFICATION_RULES = [
    ("discharge_summary", ("discharge summary", "discharge advice", "condition on discharge")),
    ("prescription", ("prescription", "rx", "tablet", "capsule", "dosage", "sig:")),
    ("lab_report", ("haemogram", "hemogram", "complete blood count", "reference range", "test report", "lab report")),
    ("imaging_report", ("impression:", "findings:", "x-ray", "ct scan", "mri", "ultrasound")),
    ("insurance_document", ("policy", "claim", "insurer", "pre-authorisation", "pre-authorization")),
    ("medical_certificate", ("medical certificate", "certify", "fit to resume")),
    ("referral_letter", ("referral", "kindly evaluate", "referred to")),
    ("consultation_note", ("chief complaint", "history of present illness", "consultation")),
]


def _sentences(text):
    raw = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [sentence.strip() for sentence in raw if len(sentence.strip()) > 25]


def _keywords(text, limit=20):
    words = re.findall(r"[a-zA-Z][a-zA-Z\-]{3,}", text.lower())
    filtered = [word for word in words if word not in STOPWORDS]
    return [word for word, _ in Counter(filtered).most_common(limit)]


def _key_points(text, limit=6):
    """Rank sentences by keyword density and keep the strongest ones in order."""
    sentences = _sentences(text)
    if not sentences:
        return []
    keywords = set(_keywords(text, 30))
    scored = []
    for index, sentence in enumerate(sentences):
        words = set(re.findall(r"[a-zA-Z][a-zA-Z\-]{3,}", sentence.lower()))
        overlap = len(words & keywords)
        has_number = bool(re.search(r"\d", sentence))
        score = overlap + (0.75 if has_number else 0) + (1.0 if index < 3 else 0)
        scored.append((score, index, sentence))
    scored.sort(key=lambda row: (-row[0], row[1]))
    chosen = sorted(scored[:limit], key=lambda row: row[1])
    return [sentence for _, _, sentence in chosen]


def extract_medications(text):
    """Find medication mentions and their dosage text."""
    found = {}
    lowered = text.lower()

    for name in KNOWN_MEDICATIONS:
        for match in re.finditer(rf"\b{re.escape(name)}\b", lowered):
            start = max(0, match.start() - 30)
            window = text[start : match.end() + 60].strip()
            dosage = re.search(
                r"(\d+(?:\.\d+)?\s?(?:mg|mcg|g|ml|iu|units?))", window, re.IGNORECASE
            )
            frequency = re.search(
                r"(once|twice|thrice|bd|b\.d\.|od|o\.d\.|tds|t\.d\.s\.|qid|q\.i\.d\.|"
                r"hs|sos|prn|every\s+\d+\s+hours?|daily|weekly)",
                window,
                re.IGNORECASE,
            )
            key = name.title()
            if key not in found:
                found[key] = {
                    "name": key,
                    "dosage": dosage.group(1) if dosage else "",
                    "frequency": frequency.group(1) if frequency else "",
                    "context": window[:160],
                }

    # Structured forms such as "Tab. Amlodipine 5 mg 1-0-1"
    pattern = re.compile(
        r"\b(?:tab|tablet|cap|capsule|inj|injection|syp|syrup)\b\.?\s*"
        r"([A-Z][A-Za-z0-9\-]{2,25})\b(?:\s+([\d.]+\s?(?:mg|mcg|g|ml|iu)))?",
        re.IGNORECASE,
    )
    for match in pattern.finditer(text):
        key = match.group(1).title()
        if key.lower() in {"the", "and", "for"}:
            continue
        entry = found.setdefault(
            key,
            {"name": key, "dosage": "", "frequency": "", "context": match.group(0)},
        )
        if match.group(2) and not entry["dosage"]:
            entry["dosage"] = match.group(2).strip()
    return list(found.values())[:25]


def extract_lab_values(text):
    """Pull analyte/value/unit triples out of the document text."""
    values = []
    for analyte in LAB_ANALYTES:
        pattern = re.compile(
            rf"\b{re.escape(analyte)}\b[^0-9\n]{{0,30}}"
            r"(-?\d+(?:\.\d+)?)\s*([a-zA-Z%/µ]+(?:/[a-zA-Z]+)?)?",
            re.IGNORECASE,
        )
        for match in pattern.finditer(text):
            value = match.group(1)
            unit = (match.group(2) or "").strip()
            context = text[max(0, match.start()) : match.end() + 40].strip()
            reference = re.search(
                rf"{re.escape(value)}[^\n]{{0,40}}?\(([^)]*\d[^)]*)\)", text
            )
            values.append(
                {
                    "name": analyte.title(),
                    "value": value,
                    "unit": unit,
                    "reference_range": reference.group(1).strip() if reference else "",
                    "context": context[:160],
                }
            )
    # De-duplicate on name + value
    seen = set()
    unique = []
    for item in values:
        key = (item["name"].lower(), item["value"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique[:30]


def extract_dates(text):
    dates = []
    for pattern in DATE_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            snippet = text[max(0, match.start() - 40) : match.end() + 20].strip()
            dates.append({"date": match.group(0), "context": snippet[:160]})
    seen = set()
    unique = []
    for item in dates:
        if item["date"] in seen:
            continue
        seen.add(item["date"])
        unique.append(item)
    return unique[:20]


def classify_document(text, fallback=""):
    lowered = text.lower()
    scores = []
    for label, keywords in CLASSIFICATION_RULES:
        score = sum(1 for keyword in keywords if keyword in lowered)
        if score:
            scores.append((score, label))
    if not scores:
        return fallback or "other"
    scores.sort(reverse=True)
    return scores[0][1]


def build_summary(text, category_hint=""):
    """
    Produce the administrative summary bundle for a document.

    Returns a dictionary with the summary text, key points, extracted
    medications, lab values, dates, classification and the safety disclaimer.
    """
    cleaned = re.sub(r"[ \t]+", " ", text or "").strip()
    if not cleaned:
        return {
            "summary": (
                "No machine-readable text was found in this document. The file is "
                "stored and available for review by an authorised professional."
            ),
            "key_points": [],
            "medications": [],
            "lab_values": [],
            "important_dates": [],
            "classification": category_hint or "other",
            "provider": "demo",
            "disclaimer": AI_DISCLAIMER,
        }

    points = _key_points(cleaned)
    medications = extract_medications(cleaned)
    labs = extract_lab_values(cleaned)
    dates = extract_dates(cleaned)
    classification = classify_document(cleaned, category_hint)

    summary_lines = []
    summary_lines.append(
        f"This document contains {len(_sentences(cleaned))} section(s) of text "
        f"({len(cleaned.split())} words) and is classified as "
        f"{classification.replace('_', ' ')}."
    )
    if points:
        summary_lines.append("Document overview: " + " ".join(points[:3]))
    if medications:
        names = ", ".join(item["name"] for item in medications[:8])
        summary_lines.append(f"Medications mentioned: {names}.")
    if labs:
        summary_lines.append(
            f"{len(labs)} laboratory value(s) were detected and listed for review."
        )
    if dates:
        summary_lines.append(
            "Dates mentioned: " + ", ".join(item["date"] for item in dates[:6]) + "."
        )

    return {
        "summary": "\n\n".join(summary_lines),
        "key_points": points,
        "medications": medications,
        "lab_values": labs,
        "important_dates": dates,
        "classification": classification,
        "provider": "demo",
        "disclaimer": AI_DISCLAIMER,
    }


def _openai_summary(text, category_hint=""):
    """Call the configured OpenAI model. Returns None when unavailable."""
    if not (settings.AI_PROVIDER == "openai" and settings.OPENAI_API_KEY):
        return None

    system_prompt = (
        "You are an administrative medical-records assistant. You organise and "
        "summarise information that appears in a document. You must never "
        "diagnose, prescribe, recommend treatment or make clinical decisions. "
        "Reply with strict JSON using the keys: summary, key_points, "
        "medications, lab_values, important_dates, classification. "
        "array items must be objects with a 'name' and 'context' where relevant."
    )
    user_prompt = (
        f"Document category hint: {category_hint or 'unknown'}.\n\n"
        f"Document text:\n{text[:12000]}"
    )

    body = json.dumps(
        {
            "model": settings.OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
    ).encode("utf-8")

    base = settings.OPENAI_BASE_URL or "https://api.openai.com/v1"
    request = urllib.request.Request(
        f"{base.rstrip('/')}/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=settings.AI_REQUEST_TIMEOUT) as response:
            payload = json.loads(response.read().decode("utf-8"))
        content = payload["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except (urllib.error.URLError, KeyError, ValueError, TimeoutError) as exc:
        logger.warning("OpenAI summarisation failed, falling back to demo engine: %s", exc)
        return None

    return {
        "summary": parsed.get("summary", ""),
        "key_points": parsed.get("key_points", []),
        "medications": parsed.get("medications", []),
        "lab_values": parsed.get("lab_values", []),
        "important_dates": parsed.get("important_dates", []),
        "classification": parsed.get("classification", category_hint or "other"),
        "provider": "openai",
        "disclaimer": AI_DISCLAIMER,
    }


def summarise_document(text, category_hint=""):
    """Try the configured provider, always fall back to the local engine."""
    if settings.AI_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        result = _openai_summary(text, category_hint)
        if result is not None:
            return result
    return build_summary(text, category_hint)


def answer_status():
    """Health information for the AI settings panel."""
    live = bool(settings.AI_PROVIDER == "openai" and settings.OPENAI_API_KEY)
    return {
        "provider": "openai" if live else "demo",
        "live_model": settings.OPENAI_MODEL if live else None,
        "disclaimer": AI_DISCLAIMER,
        "message": (
            "Live AI provider configured."
            if live
            else "Demo mode is enabled: summaries are produced locally with the "
            "built-in extractive engine. Set OPENAI_API_KEY to use a hosted model."
        ),
    }
