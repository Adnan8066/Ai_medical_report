# Query handlers for the hospital assistant.
#
# Each handler answers from the application's own database, respecting the
# caller's role matrix and patient scoping. None of them interpret clinical
# meaning: they list, count and summarise operational records only.

from datetime import date, timedelta

from django.db.models import F, Sum

from documents.services.ai import AI_DISCLAIMER


def permitted(user, module):
    return user.has_module_permission(module, "view")


def denied(module):
    return {
        "intent": "denied",
        "answer": (
            f"Your role does not have permission to view {module} data. "
            "Contact a hospital administrator if you need access."
        ),
        "data": {},
        "sources": [],
        "disclaimer": AI_DISCLAIMER,
    }


def patient_scope(user):
    """Return the linked patient record when the caller is a patient."""
    if getattr(user, "role", "") == "patient":
        return getattr(user, "patient_profile", None)
    return None


def render(rows, formatter, empty_message):
    if not rows:
        return empty_message
    return "\n".join(formatter(row) for row in rows)


def match_department(text):
    """Find a department name mentioned in the question."""
    from hospital.models import Department

    lowered = text.lower()
    for department in Department.objects.all():
        if department.name.lower() in lowered:
            return department
    return None


def appointments(user, lowered):
    if not permitted(user, "appointments"):
        return denied("appointment")
    from appointments.models import Appointment

    target = date.today() + timedelta(days=1) if "tomorrow" in lowered else date.today()
    queryset = Appointment.objects.filter(date=target).select_related("patient", "doctor")
    profile = patient_scope(user)
    if profile is not None:
        queryset = queryset.filter(patient=profile)

    rows = list(queryset[:25])
    listing = render(
        rows,
        lambda row: "- {} {} with {} ({})".format(
            row.time.strftime("%H:%M"),
            row.patient.name,
            row.doctor.name,
            row.get_status_display(),
        ),
        "There are no appointments on {}.".format(target.strftime("%d %b %Y")),
    )
    return {
        "intent": "appointments",
        "answer": "{} appointment(s) on {}:\n{}".format(
            queryset.count(), target.strftime("%d %b %Y"), listing
        ),
        "data": {
            "date": str(target),
            "count": queryset.count(),
            "results": [
                {
                    "appointment_id": row.appointment_id,
                    "patient": row.patient.name,
                    "doctor": row.doctor.name,
                    "time": row.time.strftime("%H:%M"),
                    "status": row.get_status_display(),
                    "department": row.department.name if row.department else None,
                }
                for row in rows
            ],
        },
        "sources": [{"module": "appointments", "filter": "date=" + str(target)}],
    }


def beds(user, lowered):
    if not permitted(user, "beds"):
        return denied("bed")
    from beds.models import Bed

    queryset = Bed.objects.select_related("ward", "patient").all()
    if "icu" in lowered:
        queryset = queryset.filter(category=Bed.Category.ICU)
    available = queryset.filter(status=Bed.Status.AVAILABLE)
    sample = list(available[:25])
    listing = render(
        sample,
        lambda bed: "- {} ({}, {})".format(
            bed.bed_number,
            bed.get_category_display(),
            bed.ward.name if bed.ward else "unassigned ward",
        ),
        "No beds are currently available in this category.",
    )
    total = queryset.count()
    occupied = queryset.filter(status=Bed.Status.OCCUPIED).count()
    rate = round(100 * occupied / total) if total else 0
    return {
        "intent": "beds",
        "answer": "{} of {} beds are available ({} occupied, occupancy {}%).\n{}".format(
            available.count(), total, occupied, rate, listing
        ),
        "data": {
            "total": total,
            "available": available.count(),
            "occupied": occupied,
            "reserved": queryset.filter(status=Bed.Status.RESERVED).count(),
            "maintenance": queryset.filter(status=Bed.Status.MAINTENANCE).count(),
            "beds": [
                {
                    "bed_number": bed.bed_number,
                    "category": bed.get_category_display(),
                    "ward": bed.ward.name if bed.ward else None,
                    "floor": bed.floor,
                }
                for bed in sample
            ],
        },
        "sources": [{"module": "beds", "filter": "status=available"}],
    }


def emergency(user, lowered):
    if not permitted(user, "emergency"):
        return denied("emergency")
    from emergency.models import EmergencyVisit

    queryset = EmergencyVisit.objects.filter(
        arrival_time__date=date.today()
    ).select_related("patient", "assigned_doctor")
    profile = patient_scope(user)
    if profile is not None:
        queryset = queryset.filter(patient=profile)

    rows = list(queryset[:25])
    listing = render(
        rows,
        lambda row: "- {} {} | {} | {} | waiting {} min".format(
            row.case_id,
            row.patient.name,
            row.get_priority_display(),
            row.get_status_display(),
            row.waiting_minutes,
        ),
        "There are no emergency cases registered today.",
    )
    critical = queryset.filter(priority=EmergencyVisit.Priority.CRITICAL).count()
    return {
        "intent": "emergency",
        "answer": "{} emergency case(s) today, {} critical.\n{}".format(
            queryset.count(), critical, listing
        ),
        "data": {
            "count": queryset.count(),
            "critical": critical,
            "results": [
                {
                    "case_id": row.case_id,
                    "patient": row.patient.name,
                    "priority": row.get_priority_display(),
                    "status": row.get_status_display(),
                    "doctor": row.assigned_doctor.name if row.assigned_doctor else None,
                    "waiting_minutes": row.waiting_minutes,
                }
                for row in rows
            ],
        },
        "sources": [{"module": "emergency", "filter": "arrival_time=today"}],
    }


def laboratory(user, lowered):
    if not permitted(user, "laboratory"):
        return denied("laboratory")
    from laboratory.models import LabReport

    pending_statuses = [
        LabReport.Status.ORDERED,
        LabReport.Status.SAMPLE_COLLECTED,
        LabReport.Status.PROCESSING,
    ]
    queryset = LabReport.objects.select_related("patient", "test").all()
    if "pending" in lowered or "waiting" in lowered:
        queryset = queryset.filter(status__in=pending_statuses)
    profile = patient_scope(user)
    if profile is not None:
        queryset = queryset.filter(patient=profile)

    rows = list(queryset[:25])
    listing = render(
        rows,
        lambda row: "- {} {} | {} | {}".format(
            row.lab_id,
            row.patient.name,
            row.test.name if row.test else "Test",
            row.get_status_display(),
        ),
        "No laboratory reports match that question.",
    )
    return {
        "intent": "laboratory",
        "answer": "{} laboratory report(s):\n{}".format(queryset.count(), listing),
        "data": {
            "count": queryset.count(),
            "pending": LabReport.objects.filter(status__in=pending_statuses).count(),
            "results": [
                {
                    "lab_id": row.lab_id,
                    "patient": row.patient.name,
                    "test": row.test.name if row.test else None,
                    "status": row.get_status_display(),
                    "flag": row.get_flag_display(),
                }
                for row in rows
            ],
        },
        "sources": [{"module": "laboratory", "filter": "status=pending"}],
    }


def admissions(user, lowered):
    if not permitted(user, "admissions"):
        return denied("admission")
    from admissions.models import Admission

    queryset = Admission.objects.filter(
        status__in=[
            Admission.Status.ADMITTED,
            Admission.Status.UNDER_TREATMENT,
            Admission.Status.READY_FOR_DISCHARGE,
        ]
    ).select_related("patient", "doctor", "department")

    department = match_department(lowered)
    if department is not None:
        queryset = queryset.filter(department=department)
    profile = patient_scope(user)
    if profile is not None:
        queryset = queryset.filter(patient=profile)

    rows = list(queryset[:25])
    listing = render(
        rows,
        lambda row: "- {} {} | {} | bed {} | {}".format(
            row.admission_id,
            row.patient.name,
            row.department.name if row.department else "-",
            row.bed_number or "-",
            row.get_status_display(),
        ),
        "No current inpatients match that query.",
    )
    scope = " under " + department.name if department else ""
    return {
        "intent": "admissions",
        "answer": "{} current inpatient(s){}:\n{}".format(
            queryset.count(), scope, listing
        ),
        "data": {
            "count": queryset.count(),
            "department": department.name if department else None,
            "results": [
                {
                    "admission_id": row.admission_id,
                    "patient": row.patient.name,
                    "doctor": row.doctor.name if row.doctor else None,
                    "department": row.department.name if row.department else None,
                    "bed_number": row.bed_number,
                    "status": row.get_status_display(),
                    "length_of_stay": row.length_of_stay,
                }
                for row in rows
            ],
        },
        "sources": [{"module": "admissions", "filter": "status=current"}],
    }


def pharmacy(user, lowered):
    if not permitted(user, "pharmacy"):
        return denied("pharmacy")
    from pharmacy.models import Medicine

    queryset = Medicine.objects.all()
    if "out of stock" in lowered:
        queryset = queryset.filter(stock=0)
        label = "out of stock"
    elif "expir" in lowered:
        queryset = queryset.filter(expiry_date__lte=date.today() + timedelta(days=90))
        label = "expiring within 90 days"
    else:
        queryset = queryset.filter(stock__lte=F("reorder_level"))
        label = "at or below the reorder level"

    rows = list(queryset.order_by("stock")[:25])
    listing = render(
        rows,
        lambda row: "- {} ({}) | stock {} | reorder at {}".format(
            row.name, row.medicine_id, row.stock, row.reorder_level
        ),
        "No medicines currently match that stock condition.",
    )
    return {
        "intent": "pharmacy",
        "answer": "{} medicine(s) {}:\n{}".format(queryset.count(), label, listing),
        "data": {
            "count": queryset.count(),
            "results": [
                {
                    "medicine_id": row.medicine_id,
                    "name": row.name,
                    "stock": row.stock,
                    "reorder_level": row.reorder_level,
                    "status": row.get_status_display(),
                    "expiry_date": str(row.expiry_date) if row.expiry_date else None,
                }
                for row in rows
            ],
        },
        "sources": [{"module": "pharmacy", "filter": label}],
    }


def insurance(user, lowered):
    if not permitted(user, "insurance"):
        return denied("insurance")
    from insurance.models import InsuranceClaim

    queryset = InsuranceClaim.objects.select_related("patient", "policy__provider").all()
    profile = patient_scope(user)
    if profile is not None:
        queryset = queryset.filter(patient=profile)
    if "pending" in lowered or "review" in lowered:
        queryset = queryset.filter(
            status__in=[
                InsuranceClaim.Status.SUBMITTED,
                InsuranceClaim.Status.UNDER_REVIEW,
            ]
        )

    rows = list(queryset[:25])
    listing = render(
        rows,
        lambda row: "- {} {} | {} | {} | {}".format(
            row.claim_number,
            row.patient.name,
            row.policy.provider.name if row.policy else "-",
            row.claim_amount,
            row.get_status_display(),
        ),
        "No insurance claims match that question.",
    )
    return {
        "intent": "insurance",
        "answer": "{} insurance claim(s):\n{}".format(queryset.count(), listing),
        "data": {
            "count": queryset.count(),
            "results": [
                {
                    "claim_number": row.claim_number,
                    "patient": row.patient.name,
                    "provider": row.policy.provider.name if row.policy else None,
                    "claim_amount": str(row.claim_amount),
                    "status": row.get_status_display(),
                }
                for row in rows
            ],
        },
        "sources": [{"module": "insurance", "filter": "claims"}],
    }


def billing(user, lowered):
    if not permitted(user, "billing"):
        return denied("billing")
    from billing.models import Invoice

    queryset = Invoice.objects.select_related("patient").all()
    profile = patient_scope(user)
    if profile is not None:
        queryset = queryset.filter(patient=profile)

    if "pending" in lowered or "due" in lowered or "outstanding" in lowered:
        pending = queryset.exclude(
            payment_status__in=[
                Invoice.PaymentStatus.PAID,
                Invoice.PaymentStatus.CANCELLED,
            ]
        )
        rows = list(pending[:25])
        outstanding = sum((invoice.balance_due for invoice in pending), 0)
        listing = render(
            rows,
            lambda row: "- {} {} | {} | {}".format(
                row.invoice_number,
                row.patient.name,
                row.patient_payable,
                row.get_payment_status_display(),
            ),
            "No pending bills.",
        )
        return {
            "intent": "billing_pending",
            "answer": "{} pending invoice(s), outstanding {}.\n{}".format(
                pending.count(), outstanding, listing
            ),
            "data": {
                "count": pending.count(),
                "outstanding": str(outstanding),
                "results": [
                    {
                        "invoice_number": row.invoice_number,
                        "patient": row.patient.name,
                        "payable": str(row.patient_payable),
                        "paid": str(row.paid_amount),
                        "status": row.get_payment_status_display(),
                    }
                    for row in rows
                ],
            },
            "sources": [{"module": "billing", "filter": "status=pending"}],
        }

    today = queryset.filter(date=date.today())
    collected = today.aggregate(total=Sum("paid_amount"))["total"] or 0
    billed = today.aggregate(total=Sum("patient_payable"))["total"] or 0
    return {
        "intent": "billing",
        "answer": "Today: {} invoice(s) raised, {} billed and {} collected.".format(
            today.count(), billed, collected
        ),
        "data": {
            "invoices_today": today.count(),
            "billed_today": str(billed),
            "collected_today": str(collected),
        },
        "sources": [{"module": "billing", "filter": "date=" + str(date.today())}],
    }


def discharge(user, lowered):
    if not permitted(user, "admissions"):
        return denied("discharge")
    from admissions.models import DischargeSummary

    queryset = DischargeSummary.objects.select_related("patient", "doctor").all()
    profile = patient_scope(user)
    if profile is not None:
        queryset = queryset.filter(patient=profile)
    if "ready" in lowered or "pending" in lowered:
        queryset = queryset.filter(
            status__in=[
                DischargeSummary.Status.DRAFT,
                DischargeSummary.Status.PENDING_APPROVAL,
                DischargeSummary.Status.APPROVED,
            ]
        )
    rows = list(queryset[:25])
    listing = render(
        rows,
        lambda row: "- {} {} | {}".format(
            row.discharge_id, row.patient.name, row.get_status_display()
        ),
        "No discharge summaries match that question.",
    )
    return {
        "intent": "discharge",
        "answer": "{} discharge record(s):\n{}".format(queryset.count(), listing),
        "data": {
            "count": queryset.count(),
            "results": [
                {
                    "discharge_id": row.discharge_id,
                    "patient": row.patient.name,
                    "status": row.get_status_display(),
                    "doctor_approved": row.doctor_approved,
                }
                for row in rows
            ],
        },
        "sources": [{"module": "discharge", "filter": "summaries"}],
    }


def staff(user, lowered):
    if not permitted(user, "staff"):
        return denied("staff")
    from staff.models import ShiftAssignment

    target = date.today()
    queryset = ShiftAssignment.objects.filter(date=target).select_related(
        "staff", "shift", "department"
    )
    if "night" in lowered:
        queryset = queryset.filter(shift__name__icontains="night")
    rows = list(queryset[:40])
    listing = render(
        rows,
        lambda row: "- {} ({}) | {} | {} | {}".format(
            row.staff.name,
            row.staff.get_role_display(),
            row.shift.name,
            row.department.name if row.department else "-",
            row.get_status_display(),
        ),
        "No shift assignments found for that query.",
    )
    return {
        "intent": "staff",
        "answer": "{} shift assignment(s) on {}:\n{}".format(
            queryset.count(), target.strftime("%d %b %Y"), listing
        ),
        "data": {
            "date": str(target),
            "count": queryset.count(),
            "results": [
                {
                    "staff": row.staff.name,
                    "role": row.staff.get_role_display(),
                    "shift": row.shift.name,
                    "timing": "{} - {}".format(
                        row.shift.start_time.strftime("%H:%M"),
                        row.shift.end_time.strftime("%H:%M"),
                    ),
                    "department": row.department.name if row.department else None,
                    "status": row.get_status_display(),
                }
                for row in rows
            ],
        },
        "sources": [{"module": "staff", "filter": "date=" + str(target)}],
    }


def documents(user, lowered):
    if not permitted(user, "documents"):
        return denied("document")
    from documents.models import AISummary, MedicalDocument

    queryset = MedicalDocument.objects.select_related("patient").all()
    profile = patient_scope(user)
    if profile is not None:
        queryset = queryset.filter(patient=profile)
    rows = list(queryset[:25])
    summarised = AISummary.objects.filter(document__in=rows).count()
    listing = render(
        rows,
        lambda row: "- {} {} | {} | OCR: {}".format(
            row.document_id,
            row.title,
            row.get_category_display(),
            row.get_ocr_status_display(),
        ),
        "No documents are available for that patient.",
    )
    return {
        "intent": "documents",
        "answer": (
            "{} document(s), {} with an AI summary.\n{}\n\n"
            "Open the document assistant to ask questions about their content.".format(
                queryset.count(), summarised, listing
            )
        ),
        "data": {
            "count": queryset.count(),
            "summarised": summarised,
            "results": [
                {
                    "document_id": row.document_id,
                    "title": row.title,
                    "category": row.get_category_display(),
                    "ocr_status": row.get_ocr_status_display(),
                }
                for row in rows
            ],
        },
        "sources": [{"module": "documents", "filter": "patient documents"}],
    }


def surgery(user, lowered):
    if not permitted(user, "surgery"):
        return denied("surgery")
    from surgery.models import Surgery

    queryset = Surgery.objects.filter(date__gte=date.today()).select_related(
        "patient", "surgeon"
    )
    profile = patient_scope(user)
    if profile is not None:
        queryset = queryset.filter(patient=profile)
    rows = list(queryset[:25])
    listing = render(
        rows,
        lambda row: "- {} {} | {} | {} {} | {}".format(
            row.surgery_id,
            row.patient.name,
            row.surgery_name,
            row.ot_room,
            row.start_time.strftime("%H:%M"),
            row.get_status_display(),
        ),
        "No upcoming surgeries match that question.",
    )
    return {
        "intent": "surgery",
        "answer": "{} upcoming surgery(ies):\n{}".format(queryset.count(), listing),
        "data": {
            "count": queryset.count(),
            "results": [
                {
                    "surgery_id": row.surgery_id,
                    "patient": row.patient.name,
                    "surgeon": row.surgeon.name,
                    "ot_room": row.ot_room,
                    "date": str(row.date),
                    "status": row.get_status_display(),
                }
                for row in rows
            ],
        },
        "sources": [{"module": "surgery", "filter": "upcoming"}],
    }


def bloodbank(user, lowered):
    if not permitted(user, "bloodbank"):
        return denied("blood bank")
    from bloodbank.models import BloodStock

    rows = list(BloodStock.objects.all())
    listing = "\n".join(
        "- {}: {} available, {} reserved ({})".format(
            item.blood_group, item.units_available, item.units_reserved, item.status
        )
        for item in rows
    )
    critical = [
        item.blood_group
        for item in rows
        if item.status in {"critical", "out_of_stock"}
    ]
    tail = ", ".join(critical) if critical else "All groups are adequately stocked."
    prefix = "Critical: " if critical else ""
    return {
        "intent": "bloodbank",
        "answer": "Blood bank stock:\n{}\n\n{}{}".format(listing, prefix, tail),
        "data": {
            "stock": [
                {
                    "blood_group": item.blood_group,
                    "available": item.units_available,
                    "reserved": item.units_reserved,
                    "status": item.status,
                }
                for item in rows
            ],
            "critical_groups": critical,
        },
        "sources": [{"module": "bloodbank", "filter": "stock"}],
    }
