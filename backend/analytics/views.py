# Analytics and global search endpoints.
#
# Every number returned here is calculated from the live database - nothing is
# hard-coded - so the dashboard reflects whatever is actually stored.

from datetime import date, timedelta

from django.db.models import Count, Q, Sum
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from documents.services.ai import AI_DISCLAIMER


def _series(queryset, field, days=30, value_field=None, datetime_field=False):
    """Build a dense date series so charts have no gaps."""
    start = date.today() - timedelta(days=days - 1)
    lookup_key = f"{field}__date" if datetime_field else field
    rows = (
        queryset.filter(**{f"{lookup_key}__gte": start})
        .values(lookup_key)
        .annotate(total=Count("id"), value=Sum(value_field) if value_field else Count("id"))
        .order_by(lookup_key)
    )
    lookup = {row[lookup_key]: row for row in rows}
    series = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        row = lookup.get(day)
        series.append(
            {
                "date": day.strftime("%Y-%m-%d"),
                "label": day.strftime("%d %b"),
                "total": row["total"] if row else 0,
                "value": float(row["value"] or 0) if row else 0,
            }
        )
    return series


class DashboardView(APIView):
    """Headline KPIs for the main dashboard."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from admissions.models import Admission, DischargeSummary
        from appointments.models import Appointment
        from beds.models import Bed
        from billing.models import Invoice
        from emergency.models import EmergencyVisit
        from insurance.models import InsuranceClaim
        from laboratory.models import LabReport
        from patients.models import Patient
        from pharmacy.models import Medicine
        from radiology.models import RadiologyReport
        from staff.models import ShiftAssignment
        from surgery.models import Surgery

        today = date.today()
        user = request.user

        beds = Bed.objects.all()
        bed_total = beds.count()
        bed_occupied = beds.filter(status=Bed.Status.OCCUPIED).count()
        icu = beds.filter(category=Bed.Category.ICU)
        icu_total = icu.count()
        icu_occupied = icu.filter(status=Bed.Status.OCCUPIED).count()

        revenue_today = (
            Invoice.objects.filter(date=today).aggregate(total=Sum("paid_amount"))["total"] or 0
        )
        billed_today = (
            Invoice.objects.filter(date=today).aggregate(total=Sum("patient_payable"))["total"]
            or 0
        )
        pending_invoices = Invoice.objects.exclude(
            payment_status__in=[Invoice.PaymentStatus.PAID, Invoice.PaymentStatus.CANCELLED]
        )

        payload = {
            "generated_at": today,
            "demo_mode": True,
            "kpis": {
                "total_patients": Patient.objects.count(),
                "todays_appointments": Appointment.objects.filter(date=today).count(),
                "current_inpatients": Admission.objects.filter(
                    status__in=[
                        Admission.Status.ADMITTED,
                        Admission.Status.UNDER_TREATMENT,
                        Admission.Status.READY_FOR_DISCHARGE,
                    ]
                ).count(),
                "emergency_patients": EmergencyVisit.objects.filter(
                    arrival_time__date=today
                ).count(),
                "available_beds": beds.filter(status=Bed.Status.AVAILABLE).count(),
                "total_beds": bed_total,
                "occupied_beds": bed_occupied,
                "bed_occupancy_rate": round(100 * bed_occupied / bed_total) if bed_total else 0,
                "icu_occupancy_rate": round(100 * icu_occupied / icu_total)
                if icu_total
                else 0,
                "icu_total": icu_total,
                "icu_occupied": icu_occupied,
                "icu_available": icu.filter(status=Bed.Status.AVAILABLE).count(),
                "pending_lab_reports": LabReport.objects.exclude(
                    status__in=[LabReport.Status.COMPLETED, LabReport.Status.CANCELLED]
                ).count(),
                "pending_radiology": RadiologyReport.objects.exclude(
                    status__in=[
                        RadiologyReport.Status.COMPLETED,
                        RadiologyReport.Status.CANCELLED,
                    ]
                ).count(),
                "pending_insurance_claims": InsuranceClaim.objects.filter(
                    status__in=[
                        InsuranceClaim.Status.SUBMITTED,
                        InsuranceClaim.Status.UNDER_REVIEW,
                    ]
                ).count(),
                "revenue_today": float(revenue_today),
                "billed_today": float(billed_today),
                "pending_bills": pending_invoices.count(),
                "outstanding_amount": float(
                    sum((invoice.balance_due for invoice in pending_invoices[:500]), 0)
                ),
                "discharges_today": Admission.objects.filter(
                    discharge_date__date=today
                ).count(),
                "ready_for_discharge": DischargeSummary.objects.filter(
                    doctor_approved=True, status=DischargeSummary.Status.APPROVED
                ).count(),
                "surgeries_today": Surgery.objects.filter(date=today).count(),
                "pharmacy_alerts": Medicine.objects.filter(
                    Q(stock__lte=models_F("reorder_level")) | Q(stock=0)
                ).count(),
                "staff_on_duty": ShiftAssignment.objects.filter(
                    date=today,
                    status__in=[
                        ShiftAssignment.Status.SCHEDULED,
                        ShiftAssignment.Status.IN_PROGRESS,
                    ],
                ).count(),
            },
        }

        if user.is_administrator or user.role in {"hod", "doctor"}:
            payload["clinical"] = {
                "critical_emergency": EmergencyVisit.objects.filter(
                    arrival_time__date=today, priority=EmergencyVisit.Priority.CRITICAL
                ).count(),
                "surgeries_in_progress": Surgery.objects.filter(
                    status=Surgery.Status.IN_PROGRESS
                ).count(),
                "abnormal_lab_flags": LabReport.objects.filter(
                    flag__in=["high", "low", "critical"]
                ).count(),
            }
        return Response(payload)


def models_F(field):
    """Tiny indirection so the F() import stays local to this module."""
    from django.db.models import F

    return F(field)


class ChartsView(APIView):
    """Data for every dashboard chart."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from admissions.models import Admission
        from appointments.models import Appointment
        from beds.models import Bed
        from billing.models import Invoice
        from emergency.models import EmergencyVisit
        from hospital.models import Department
        from laboratory.models import LabReport
        from opd.models import OPDVisit
        from patients.models import Patient
        from pharmacy.models import Medicine

        days = int(request.query_params.get("days", 30))
        start = date.today() - timedelta(days=days - 1)

        department_distribution = list(
            Patient.objects.values("department__name")
            .annotate(total=Count("id"))
            .order_by("-total")[:12]
        )
        opd_by_department = list(
            OPDVisit.objects.filter(visit_date__gte=start)
            .values("department__name")
            .annotate(total=Count("id"))
            .order_by("-total")[:12]
        )
        bed_occupancy = list(
            Bed.objects.values("category")
            .annotate(
                total=Count("id"),
                occupied=Count("id", filter=Q(status=Bed.Status.OCCUPIED)),
                available=Count("id", filter=Q(status=Bed.Status.AVAILABLE)),
            )
            .order_by("category")
        )
        revenue_series = _series(Invoice.objects.all(), "date", days, "paid_amount")
        lab_by_category = list(
            LabReport.objects.values("test__category")
            .annotate(total=Count("id"))
            .order_by("-total")
        )
        pharmacy_by_category = list(
            Medicine.objects.values("category")
            .annotate(total=Count("id"), units=Sum("stock"))
            .order_by("-total")
        )
        appointment_status = list(
            Appointment.objects.values("status").annotate(total=Count("id")).order_by("-total")
        )
        admission_status = list(
            Admission.objects.values("status").annotate(total=Count("id")).order_by("-total")
        )

        return Response(
            {
                "range_days": days,
                "patient_registration_trend": _series(Patient.objects.all(), "registration_date", days),
                "opd_trend": _series(OPDVisit.objects.all(), "visit_date", days),
                "emergency_trend": _series(
                    EmergencyVisit.objects.all(), "arrival_time", days, datetime_field=True
                ),
                "revenue_trend": revenue_series,
                "opd_by_department": opd_by_department,
                "department_distribution": department_distribution,
                "bed_occupancy": bed_occupancy,
                "lab_workload": lab_by_category,
                "pharmacy_stock": pharmacy_by_category,
                "appointment_status": appointment_status,
                "admission_status": admission_status,
                "department_count": Department.objects.count(),
            }
        )


def _linear_forecast(values, periods):
    """Least-squares trend extrapolation over a list of numeric values."""
    points = [value for value in values if value is not None]
    if len(points) < 2:
        return [round(points[-1] if points else 0, 1)] * periods
    n = len(points)
    mean_x = (n - 1) / 2
    mean_y = sum(points) / n
    numerator = sum((index - mean_x) * (value - mean_y) for index, value in enumerate(points))
    denominator = sum((index - mean_x) ** 2 for index in range(n)) or 1
    slope = numerator / denominator
    intercept = mean_y - slope * mean_x
    return [round(max(0, intercept + slope * (n - 1 + step)), 1) for step in range(1, periods + 1)]


class ForecastView(APIView):
    """
    Simple trend estimates for planning.

    These are statistical extrapolations of historical operational counts, not
    clinical predictions, and are labelled as estimates in the UI.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from beds.models import Bed
        from emergency.models import EmergencyVisit
        from laboratory.models import LabReport
        from opd.models import OPDVisit
        from patients.models import Patient
        from pharmacy.models import Medicine

        horizon = int(request.query_params.get("days", 7))
        history = int(request.query_params.get("history", 30))

        registrations = [row["total"] for row in _series(Patient.objects.all(), "registration_date", history)]
        opd_visits = [row["total"] for row in _series(OPDVisit.objects.all(), "visit_date", history)]
        emergency = [
            row["total"]
            for row in _series(
                EmergencyVisit.objects.all(), "arrival_time", history, datetime_field=True
            )
        ]
        labs = [
            row["total"]
            for row in _series(
                LabReport.objects.all(), "ordered_at", history, datetime_field=True
            )
        ]

        beds = Bed.objects.all()
        total_beds = beds.count()
        occupied = beds.filter(status=Bed.Status.OCCUPIED).count()
        current_occupancy = round(100 * occupied / total_beds) if total_beds else 0
        occupancy_points = []
        for offset in range(history, 0, -1):
            day = date.today() - timedelta(days=offset)
            admissions = beds.filter(admissions__admission_date__date__lte=day).exclude(
                admissions__discharge_date__date__lt=day
            ).count()
            if total_beds:
                occupancy_points.append(round(100 * admissions / total_beds))

        low_stock = Medicine.objects.filter(stock__lte=models_F("reorder_level"))
        return Response(
            {
                "horizon_days": horizon,
                "history_days": history,
                "estimates": {
                    "patient_registrations": {
                        "daily": _linear_forecast(registrations, horizon),
                        "history": registrations,
                        "unit": "patients per day",
                    },
                    "opd_volume": {
                        "daily": _linear_forecast(opd_visits, horizon),
                        "history": opd_visits,
                        "unit": "visits per day",
                    },
                    "emergency_workload": {
                        "daily": _linear_forecast(emergency, horizon),
                        "history": emergency,
                        "unit": "cases per day",
                    },
                    "laboratory_workload": {
                        "daily": _linear_forecast(labs, horizon),
                        "history": labs,
                        "unit": "tests per day",
                    },
                    "bed_occupancy": {
                        "current_rate": current_occupancy,
                        "projected_rate": (
                            _linear_forecast(occupancy_points, 1)[0]
                            if occupancy_points
                            else current_occupancy
                        ),
                        "history": occupancy_points,
                        "unit": "percent occupied",
                    },
                    "pharmacy_demand": {
                        "low_stock_items": low_stock.count(),
                        "top_low_stock": [
                            {
                                "name": item.name,
                                "stock": item.stock,
                                "reorder_level": item.reorder_level,
                            }
                            for item in low_stock.order_by("stock")[:10]
                        ],
                        "unit": "items below reorder level",
                    },
                },
                "disclaimer": (
                    "These figures are statistical estimates derived from historical "
                    "demo activity. They are provided for operational planning only "
                    "and must not be used for clinical decisions."
                ),
                "ai_disclaimer": AI_DISCLAIMER,
            }
        )


class GlobalSearchView(APIView):
    """
    Search across every module the caller is allowed to see.

    Each section only runs when the role matrix grants ``view`` on that module,
    and patient-scoped users only ever see their own records.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = (request.query_params.get("q") or "").strip()
        limit = min(int(request.query_params.get("limit", 5)), 20)
        if len(query) < 2:
            return Response(
                {
                    "query": query,
                    "results": {},
                    "total": 0,
                    "message": "Type at least two characters to search.",
                }
            )

        user = request.user
        results = {}
        patient = getattr(user, "patient_profile", None)
        is_patient = patient is not None

        def allowed(module):
            return user.has_module_permission(module, "view")

        if allowed("patients"):
            from patients.models import Patient

            queryset = Patient.objects.filter(
                Q(name__icontains=query)
                | Q(patient_id__icontains=query)
                | Q(phone__icontains=query)
            )
            if is_patient:
                queryset = queryset.filter(pk=patient.pk)
            results["patients"] = [
                {
                    "id": row.id,
                    "title": row.name,
                    "subtitle": f"{row.patient_id} | {row.get_current_status_display()}",
                    "url": f"/patients/{row.id}",
                }
                for row in queryset[:limit]
            ]

        if allowed("doctors"):
            from doctors.models import Doctor

            queryset = Doctor.objects.filter(
                Q(name__icontains=query)
                | Q(doctor_id__icontains=query)
                | Q(specialization__icontains=query)
            )
            results["doctors"] = [
                {
                    "id": row.id,
                    "title": row.name,
                    "subtitle": f"{row.doctor_id} | {row.department.name if row.department else ''}",
                    "url": f"/doctors/{row.id}",
                }
                for row in queryset.select_related("department")[:limit]
            ]

        if allowed("appointments"):
            from appointments.models import Appointment

            queryset = Appointment.objects.filter(
                Q(appointment_id__icontains=query)
                | Q(patient__name__icontains=query)
                | Q(reason__icontains=query)
            ).select_related("patient", "doctor")
            if is_patient:
                queryset = queryset.filter(patient=patient)
            results["appointments"] = [
                {
                    "id": row.id,
                    "title": f"{row.appointment_id} - {row.patient.name}",
                    "subtitle": f"{row.date} {row.time:%H:%M} | {row.doctor.name if row.doctor else ''}",
                    "url": f"/appointments/{row.id}",
                }
                for row in queryset[:limit]
            ]

        if allowed("documents"):
            from documents.models import MedicalDocument

            queryset = MedicalDocument.objects.filter(
                Q(title__icontains=query)
                | Q(document_id__icontains=query)
                | Q(tags__icontains=query)
                | Q(patient__name__icontains=query)
            ).select_related("patient")
            if is_patient:
                queryset = queryset.filter(patient=patient)
            results["documents"] = [
                {
                    "id": row.id,
                    "title": row.title,
                    "subtitle": f"{row.document_id} | {row.get_category_display()}",
                    "url": f"/documents/{row.id}",
                }
                for row in queryset[:limit]
            ]

        if allowed("departments"):
            from hospital.models import Department

            queryset = Department.objects.filter(
                Q(name__icontains=query) | Q(code__icontains=query)
            )
            results["departments"] = [
                {
                    "id": row.id,
                    "title": row.name,
                    "subtitle": f"{row.code} | Floor {row.floor}",
                    "url": f"/departments/{row.id}",
                }
                for row in queryset[:limit]
            ]

        if allowed("laboratory"):
            from laboratory.models import LabReport

            queryset = LabReport.objects.filter(
                Q(lab_id__icontains=query)
                | Q(patient__name__icontains=query)
                | Q(test__name__icontains=query)
            ).select_related("patient", "test")
            if is_patient:
                queryset = queryset.filter(patient=patient)
            results["laboratory"] = [
                {
                    "id": row.id,
                    "title": f"{row.lab_id} - {row.test.name if row.test else 'Test'}",
                    "subtitle": f"{row.patient.name} | {row.get_status_display()}",
                    "url": f"/laboratory/{row.id}",
                }
                for row in queryset[:limit]
            ]

        if allowed("pharmacy"):
            from pharmacy.models import Medicine

            queryset = Medicine.objects.filter(
                Q(name__icontains=query)
                | Q(medicine_id__icontains=query)
                | Q(generic_name__icontains=query)
            )
            results["medicines"] = [
                {
                    "id": row.id,
                    "title": row.name,
                    "subtitle": f"{row.medicine_id} | stock {row.stock}",
                    "url": f"/pharmacy/{row.id}",
                }
                for row in queryset[:limit]
            ]

        if allowed("billing"):
            from billing.models import Invoice

            queryset = Invoice.objects.filter(
                Q(invoice_number__icontains=query) | Q(patient__name__icontains=query)
            ).select_related("patient")
            if is_patient:
                queryset = queryset.filter(patient=patient)
            results["bills"] = [
                {
                    "id": row.id,
                    "title": f"{row.invoice_number}",
                    "subtitle": f"{row.patient.name} | {row.patient_payable} | {row.get_payment_status_display()}",
                    "url": f"/billing/{row.id}",
                }
                for row in queryset[:limit]
            ]

        total = sum(len(items) for items in results.values())
        return Response({"query": query, "results": results, "total": total})
