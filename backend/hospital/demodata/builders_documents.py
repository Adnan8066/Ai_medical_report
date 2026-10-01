# Builders for medical documents (with real, OCR-able PDFs), notifications,
# shift rosters and the audit trail.

import io
from datetime import date, timedelta

from django.core.files.base import ContentFile
from django.utils import timezone

from audit.models import AuditLog
from documents.models import MedicalDocument
from notifications.models import Notification
from staff.models import Shift, ShiftAssignment, Staff


def _escape_pdf_text(value):
    return value.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def build_pdf(lines, title="AsterNova Demo Document"):
    """
    Create a small, valid, single page PDF containing the supplied text.

    The generated file has a real text layer, so the OCR/pypdf pipeline used by
    the documents module can read it back - which makes the demo genuinely end
    to end rather than faking the extracted text.
    """
    content = ["BT", "/F1 11 Tf", "50 790 Td", "15 TL"]
    content.append("({}) Tj T*".format(_escape_pdf_text(title)))
    content.append("() Tj T*")
    for line in lines:
        content.append("({}) Tj T*".format(_escape_pdf_text(line)))
    content.append("ET")
    stream = "\n".join(content).encode("latin-1", "replace")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    buffer = io.BytesIO()
    buffer.write(b"%PDF-1.4\n")
    offsets = []
    for index, payload in enumerate(objects, start=1):
        offsets.append(buffer.tell())
        buffer.write("{} 0 obj\n".format(index).encode())
        buffer.write(payload)
        buffer.write(b"\nendobj\n")

    xref_offset = buffer.tell()
    buffer.write("xref\n0 {}\n".format(len(objects) + 1).encode())
    buffer.write(b"0000000000 65535 f \n")
    for offset in offsets:
        buffer.write("{:010d} 00000 n \n".format(offset).encode())
    buffer.write(
        "trailer\n<< /Size {} /Root 1 0 R >>\nstartxref\n{}\n%%EOF\n".format(
            len(objects) + 1, xref_offset
        ).encode()
    )
    return buffer.getvalue()


DOCUMENT_TEMPLATES = {
    "lab_report": [
        "ASTERNOVA MULTISPECIALITY HOSPITAL - DEPARTMENT OF PATHOLOGY",
        "Sample type: Blood",
        "",
        "Complete Blood Count (CBC)",
        "Hemoglobin            13.8 g/dL      Reference range 13.5 - 17.5 g/dL",
        "Total WBC count       7,400 /uL      Reference range 4,000 - 11,000 /uL",
        "Platelet count        245,000 /uL    Reference range 150,000 - 450,000 /uL",
        "",
        "Fasting Blood Glucose 112 mg/dL       Reference range 70 - 100 mg/dL",
        "HbA1c                 7.4 %           Reference range 4.0 - 5.6 %",
        "Serum Creatinine      1.1 mg/dL       Reference range 0.6 - 1.3 mg/dL",
        "",
        "Report reviewed by the duty pathologist. Demo document only.",
    ],
    "prescription": [
        "ASTERNOVA MULTISPECIALITY HOSPITAL - OUTPATIENT PRESCRIPTION",
        "",
        "Rx",
        "1. Tab. Paracetamol 500 mg - 1 tablet twice daily after food for 5 days",
        "2. Tab. Pantoprazole 40 mg - 1 tablet once daily before breakfast for 7 days",
        "3. Tab. Metformin 500 mg - 1 tablet twice daily with meals for 30 days",
        "4. Tab. Amlodipine 5 mg - 1 tablet once daily for 30 days",
        "",
        "Advice: Continue medication as prescribed. Review in the outpatient",
        "department after two weeks with previous reports.",
        "This is a fictional demonstration prescription.",
    ],
    "discharge_summary": [
        "ASTERNOVA MULTISPECIALITY HOSPITAL - DISCHARGE SUMMARY",
        "",
        "Date of admission: 12/03/2024",
        "Date of discharge: 18/03/2024",
        "",
        "Presenting complaint: Chest discomfort on exertion with breathlessness.",
        "Investigations: Complete Blood Count, Lipid Profile, Echocardiography,",
        "Coronary angiogram. Results reviewed by the treating team.",
        "Procedures performed: Coronary angiogram with stenting.",
        "",
        "Condition on discharge: Stable and ambulatory.",
        "Medications on discharge:",
        "Tab. Atorvastatin 10 mg once daily at night for 30 days",
        "Tab. Clopidogrel 75 mg once daily for 30 days",
        "Tab. Metoprolol 25 mg once daily for 30 days",
        "",
        "Follow-up instructions: Review in cardiology OPD after one week with the",
        "discharge summary and previous investigations.",
        "Demo document generated for the AsterNova showcase.",
    ],
    "imaging_report": [
        "ASTERNOVA MULTISPECIALITY HOSPITAL - DEPARTMENT OF RADIOLOGY",
        "",
        "Study: CT Brain Plain",
        "Date of study: 04/04/2024",
        "",
        "Findings: No acute intracranial haemorrhage, mass effect or midline shift.",
        "Ventricles and sulci are normal for age. No acute infarct identified.",
        "Impression: No acute intracranial abnormality in this demo study.",
        "Reported by the duty radiologist.",
    ],
    "medical_certificate": [
        "ASTERNOVA MULTISPECIALITY HOSPITAL - MEDICAL CERTIFICATE",
        "",
        "This is to certify that the patient was examined in the outpatient",
        "department and was advised rest for three days.",
        "The patient is fit to resume duties with effect from 21/04/2024.",
        "This certificate is issued for administrative purposes.",
        "Fictional demo certificate - not valid for any real purpose.",
    ],
    "referral_letter": [
        "ASTERNOVA MULTISPECIALITY HOSPITAL - REFERRAL LETTER",
        "",
        "Dear Colleague,",
        "Thank you for referring this patient for further evaluation.",
        "The patient has been assessed and preliminary investigations arranged.",
        "Kindly evaluate for specialist opinion and advise on further management.",
        "The patient has been scheduled for a review appointment after two weeks.",
        "Demo referral letter.",
    ],
    "insurance_document": [
        "ASTERNOVA MULTISPECIALITY HOSPITAL - INSURANCE CLAIM PACKET",
        "",
        "Policy number: POL-NOVA-004512",
        "Insurer: Nova Health Assure (fictional)",
        "Claim amount requested: 184500.00",
        "Admission date: 12/03/2024  Discharge date: 18/03/2024",
        "Pre-authorisation reference: PA-2024-00912",
        "",
        "Documents enclosed: discharge summary, hospital bill, investigation",
        "reports and pre-authorisation approval letter.",
        "Fictional demo insurance documentation.",
    ],
    "consultation_note": [
        "ASTERNOVA MULTISPECIALITY HOSPITAL - CONSULTATION NOTE",
        "",
        "Chief complaint: Fever with body ache for three days.",
        "History of present illness: Nocturnal cough, reduced appetite, no",
        "history of contact with infectious disease.",
        "Examination: Febrile, chest clear, abdomen soft.",
        "Investigations advised: Complete Blood Count, CRP, Urine routine.",
        "Advice: Plenty of oral fluids, antipyretic as required, review in 3 days.",
        "Demo consultation note.",
    ],
}


CATEGORY_TITLES = {
    "lab_report": "Laboratory Report",
    "prescription": "Prescription",
    "discharge_summary": "Discharge Summary",
    "imaging_report": "Imaging Report",
    "medical_certificate": "Medical Certificate",
    "referral_letter": "Referral Letter",
    "insurance_document": "Insurance Claim Packet",
    "consultation_note": "Consultation Note",
}


def _document_text(category, patient, doctor_name):
    lines = list(DOCUMENT_TEMPLATES[category])
    lines.insert(0, "Patient name: {}".format(patient.name))
    lines.insert(1, "Patient ID: {}".format(patient.patient_id))
    lines.insert(2, "Treating consultant: {}".format(doctor_name or "Duty medical officer"))
    lines.insert(3, "Document date: {}".format(timezone.now().strftime("%d/%m/%Y")))
    lines.append("Department: {}".format(patient.department.name if patient.department else "-"))
    return lines


def seed_documents(patients, rng, limit=220):
    """Create real PDF documents for a large slice of the patient population."""
    from documents.pipeline import process_document

    categories = list(DOCUMENT_TEMPLATES.keys())
    created = 0
    processed = 0
    counter = 10001
    candidates = list(patients)
    rng.shuffle(candidates)

    for patient in candidates[:limit]:
        for _ in range(rng.randint(1, 2)):
            category = rng.choice(categories)
            document_id = "DOC-{}".format(counter)
            counter += 1
            doctor_name = patient.assigned_doctor.name if patient.assigned_doctor else ""
            lines = _document_text(category, patient, doctor_name)
            payload = build_pdf(lines, title=CATEGORY_TITLES[category])

            document = MedicalDocument.objects.filter(document_id=document_id).first()
            already_stored = document is not None and bool(document.file)
            if document is None:
                document = MedicalDocument(document_id=document_id)
            document.patient = patient
            document.category = category
            document.title = "{} - {}".format(
                CATEGORY_TITLES[category], patient.patient_id
            )
            document.description = "Fictional demo document generated for the showcase."
            document.document_date = (date.today() - timedelta(days=rng.randint(0, 60)))
            document.tags = "{},demo,{}".format(category, patient.department.code if patient.department else "general")
            document.original_filename = "{}.pdf".format(document_id.lower())
            document.mime_type = "application/pdf"
            document.is_demo = True
            document.save()

            if not already_stored:
                content = ContentFile(payload, name="{}.pdf".format(document_id.lower()))
                document.file.save(content.name, content, save=True)
                document.file_size = document.file.size
                import hashlib

                digest = hashlib.sha256()
                document.file.open("rb")
                for chunk in document.file.chunks():
                    digest.update(chunk)
                document.file.close()
                document.checksum = digest.hexdigest()
                document.save(update_fields=["file_size", "checksum"])

            process_document(document)
            processed += 1
            created += 1

    # Deliberate duplicate so the duplicate detection feature has something to find.
    if len(candidates) >= 2:
        original = MedicalDocument.objects.filter(patient=candidates[0]).first()
        if original is not None:
            duplicate, _ = MedicalDocument.objects.update_or_create(
                document_id="DOC-{}".format(counter),
                defaults={
                    "patient": candidates[0],
                    "category": original.category,
                    "title": "Duplicate copy - {}".format(original.title),
                    "description": "Uploaded twice to demonstrate duplicate detection.",
                    "original_filename": original.original_filename,
                    "mime_type": "application/pdf",
                    "checksum": original.checksum,
                },
            )
            if not duplicate.file:
                duplicate.file.save(
                    "doc-{}.pdf".format(counter), ContentFile(build_pdf(["Duplicate"])), save=True
                )
            process_document(duplicate)
            created += 1

    return {"documents": created, "processed": processed}


NOTIFICATION_TEMPLATES = [
    ("Dr. Meera Nair has an appointment in 15 minutes.", "appointment", "info", "/appointments"),
    ("ICU bed ICU-006 is now available.", "bed", "success", "/beds"),
    ("Laboratory report for PAT-10023 is ready.", "laboratory", "success", "/laboratory"),
    ("Pharmacy item stock is below the reorder level.", "pharmacy", "warning", "/pharmacy"),
    ("Patient PAT-10042 is ready for discharge.", "discharge", "info", "/admissions"),
    ("Emergency case ER-01004 has been triaged as critical.", "admission", "critical", "/emergency"),
    ("Insurance claim CLM-01003 requires documentation.", "insurance", "warning", "/insurance"),
    ("New medical document uploaded and OCR completed.", "document", "success", "/documents"),
    ("Bed G-114 has been discharged and requires cleaning.", "bed", "info", "/beds"),
    ("Monthly biomedical equipment calibration is due.", "inventory", "warning", "/inventory"),
    ("Blood bank stock for B- is below the critical threshold.", "pharmacy", "critical", "/blood-bank"),
    ("Shift handover summary for the night shift is pending.", "system", "info", "/staff"),
    ("Outstanding invoices exceed the daily threshold.", "billing", "warning", "/billing"),
    ("AI summary generated for a newly uploaded discharge summary.", "ai", "info", "/documents"),
]


def seed_notifications(users_by_username, rng):
    """Create the notification feed shown in the header bell."""
    Notification.objects.filter(is_demo=True).delete()
    created = 0
    counter = 1001
    recipients = [
        users_by_username.get("admin"),
        users_by_username.get("doctor"),
        users_by_username.get("nurse"),
        users_by_username.get("reception"),
        users_by_username.get("pharmacist"),
        users_by_username.get("labtech"),
        None,
    ]
    for index in range(48):
        title, category, level, link = NOTIFICATION_TEMPLATES[index % len(NOTIFICATION_TEMPLATES)]
        recipient = rng.choice(recipients)
        Notification.objects.create(
            recipient=recipient,
            role_target="" if recipient else rng.choice(["", "doctor", "nurse"]),
            title=title,
            message="{} (fictional demo notification)".format(title),
            category=category,
            level=level,
            is_read=rng.random() < 0.45,
            link=link,
            expires_at=timezone.now() + timedelta(days=30),
        )
        counter += 1
        created += 1
    return created


def seed_shift_assignments(rng, days=5):
    """Build a roster covering recent and upcoming days."""
    staff = list(Staff.objects.select_related("department", "shift").all())
    shifts = list(Shift.objects.all())
    if not staff or not shifts:
        return 0
    created = 0
    today = date.today()
    for offset in range(-days + 1, days + 1):
        target = today + timedelta(days=offset)
        for member in staff:
            shift = member.shift or rng.choice(shifts)
            if target < today:
                status = ShiftAssignment.Status.COMPLETED
            elif target == today:
                status = rng.choice(
                    [ShiftAssignment.Status.IN_PROGRESS, ShiftAssignment.Status.SCHEDULED]
                )
            else:
                status = ShiftAssignment.Status.SCHEDULED
            ShiftAssignment.objects.update_or_create(
                staff=member,
                shift=shift,
                date=target,
                defaults={
                    "department": member.department,
                    "ward": rng.choice(
                        ["General Ward", "ICU", "Emergency", "OPD", "Theatre"]
                    ),
                    "status": status,
                    "notes": "Auto-generated demo roster entry.",
                },
            )
            created += 1
    return created


AUDIT_TEMPLATES = [
    ("Created doctor DOC-1020", "doctors", "info"),
    ("Registered patient PAT-10051", "patients", "info"),
    ("Viewed patient record PAT-10017", "patients", "info"),
    ("Uploaded medical document DOC-10012", "documents", "info"),
    ("Updated medicine stock MED-1012", "pharmacy", "info"),
    ("Approved discharge summary DS-01004", "admissions", "info"),
    ("Updated role permissions for Nurse", "users", "warning"),
    ("Issued blood units BIS-01012", "bloodbank", "info"),
    ("Recorded payment for invoice INV-01120", "billing", "info"),
    ("Updated insurance claim CLM-01044", "insurance", "info"),
    ("Failed login attempt", "users", "warning"),
    ("Processed purchase order PO-01004", "inventory", "info"),
]


def seed_audit_logs(users_by_username, rng):
    """Backfill an audit trail so the audit screen is not empty."""
    AuditLog.objects.filter(user_agent="Demo seed script").delete()
    created = 0
    usernames = [
        "admin",
        "hospitaladmin",
        "doctor",
        "nurse",
        "reception",
        "pharmacist",
        "labtech",
        "billing",
        "insurance",
        "inventory",
    ]
    for index in range(70):
        action, module, severity = AUDIT_TEMPLATES[index % len(AUDIT_TEMPLATES)]
        username = rng.choice(usernames)
        user = users_by_username.get(username)
        entry = AuditLog.objects.create(
            user=user,
            username=username,
            role=getattr(user, "role", "") if user else "",
            action=action,
            module=module,
            severity=severity,
            description="{}.".format(action),
            ip_address="127.0.0.1",
            user_agent="Demo seed script",
            method=rng.choice(["POST", "PATCH", "GET", "DELETE"]),
            path="/api/{}/".format(module),
        )
        AuditLog.objects.filter(pk=entry.pk).update(
            created_at=timezone.now()
            - timedelta(hours=rng.randint(1, 240), minutes=rng.randint(0, 59))
        )
        created += 1
    return created
