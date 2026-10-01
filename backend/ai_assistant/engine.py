# Router for the hospital assistant.
#
# The assistant answers strictly from the application's own database using the
# caller's role matrix (see handlers.py). It never diagnoses, prescribes or
# recommends treatment.

from documents.services.ai import AI_DISCLAIMER

from . import handlers

SUGGESTED_QUESTIONS = [
    "What appointments are scheduled today?",
    "Which beds are available?",
    "Show today's emergency patients.",
    "Which patients are waiting for laboratory reports?",
    "Show patients admitted under Cardiology.",
    "Which medicines are low in stock?",
    "Summarize this patient's uploaded documents.",
    "How many insurance claims are pending?",
    "Which staff are on the night shift today?",
    "Show upcoming surgeries.",
]

INTENT_ROUTES = [
    (("appointment", "opd schedule", "scheduled today"), handlers.appointments),
    (("bed", "icu", "occupancy", "ward"), handlers.beds),
    (("emergency", "casualty", "triage"), handlers.emergency),
    (("laboratory", "lab report", "blood test", "pending reports", "report"), handlers.laboratory),
    (("admitted", "admission", "inpatient", "ipd"), handlers.admissions),
    (("medicine", "pharmacy", "stock", "drug"), handlers.pharmacy),
    (("claim", "insurance"), handlers.insurance),
    (("bill", "invoice", "revenue", "payment", "outstanding"), handlers.billing),
    (("discharge",), handlers.discharge),
    (("staff", "shift", "roster", "on duty"), handlers.staff),
    (("document", "summar"), handlers.documents),
    (("surgery", "operation theatre", "operation"), handlers.surgery),
    (("blood", "transfusion"), handlers.bloodbank),
]


def route(question):
    """Pick the first handler whose keywords appear in the question."""
    lowered = (question or "").lower()
    for keywords, handler in INTENT_ROUTES:
        if any(keyword in lowered for keyword in keywords):
            return handler
    return None


def answer_question(question, user):
    """Return a structured, authorised answer for the assistant UI."""
    text = (question or "").strip()
    if not text:
        return {
            "intent": "empty",
            "answer": "Ask a question about appointments, beds, laboratory work, "
            "pharmacy stock, billing, insurance, staff, surgery or documents.",
            "data": {},
            "sources": [],
            "suggestions": SUGGESTED_QUESTIONS[:5],
            "disclaimer": AI_DISCLAIMER,
        }

    handler = route(text)
    if handler is None:
        result = {
            "intent": "unknown",
            "answer": (
                "I can help with operational questions about appointments, beds, "
                "emergency cases, laboratory work, admissions, pharmacy stock, "
                "billing, insurance, staff shifts, surgery and uploaded documents. "
                "Try one of the suggested questions below."
            ),
            "data": {},
            "sources": [],
        }
    else:
        result = handler(user, text.lower())

    result.setdefault("suggestions", SUGGESTED_QUESTIONS[:5])
    result["disclaimer"] = AI_DISCLAIMER
    result["question"] = text
    return result
