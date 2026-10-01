from django.db.models import Count
from rest_framework.decorators import action
from rest_framework.response import Response

from config.viewsets import BaseViewSet

from .models import NurseAssignment, Patient, Vitals
from .serializers import (
    NurseAssignmentSerializer,
    PatientListSerializer,
    PatientSerializer,
    PatientWriteSerializer,
    VitalsSerializer,
)


class PatientViewSet(BaseViewSet):
    module = "patients"
    queryset = Patient.objects.select_related("department", "assigned_doctor").all()
    search_fields = ["name", "patient_id", "phone", "email", "insurance_policy_number"]
    ordering_fields = ["name", "registration_date", "patient_id"]
    ordering = ["name"]
    apply_patient_scope = True
    patient_lookup = "id"

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return PatientWriteSerializer
        if self.action == "list":
            return PatientListSerializer
        return PatientSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        if department := params.get("department"):
            queryset = queryset.filter(department_id=department)
        if doctor := params.get("doctor"):
            queryset = queryset.filter(assigned_doctor_id=doctor)
        if patient_type := params.get("patient_type"):
            queryset = queryset.filter(patient_type=patient_type)
        if status_value := params.get("status"):
            queryset = queryset.filter(current_status=status_value)
        if admission_status := params.get("admission_status"):
            queryset = queryset.filter(admission_status=admission_status)
        if gender := params.get("gender"):
            queryset = queryset.filter(gender=gender)
        if blood_group := params.get("blood_group"):
            queryset = queryset.filter(blood_group=blood_group)
        return queryset

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Headline patient statistics derived live from the database."""
        queryset = self.get_queryset()
        by_department = (
            queryset.values("department__name")
            .annotate(total=Count("id"))
            .order_by("-total")
        )
        return Response(
            {
                "total": queryset.count(),
                "opd": queryset.filter(patient_type=Patient.PatientType.OPD).count(),
                "inpatients": queryset.filter(
                    patient_type=Patient.PatientType.INPATIENT
                ).count(),
                "emergency": queryset.filter(
                    patient_type=Patient.PatientType.EMERGENCY
                ).count(),
                "icu": queryset.filter(patient_type=Patient.PatientType.ICU).count(),
                "discharged": queryset.filter(
                    current_status=Patient.Status.DISCHARGED
                ).count(),
                "admitted": queryset.filter(
                    admission_status=Patient.AdmissionStatus.ADMITTED
                ).count(),
                "by_department": [
                    {
                        "department": row["department__name"] or "Unassigned",
                        "total": row["total"],
                    }
                    for row in by_department
                ],
            }
        )

    @action(detail=True, methods=["get"])
    def timeline(self, request, pk=None):
        """
        Chronological clinical timeline for the patient profile screen.

        Aggregates events from every module so the profile page can render a
        single professional timeline.
        """
        patient = self.get_object()
        events = []

        def add(event_type, date_value, title, description="", status="", link=""):
            if not date_value:
                return
            events.append(
                {
                    "type": event_type,
                    "date": date_value,
                    "title": title,
                    "description": description,
                    "status": status,
                    "link": link,
                }
            )

        add(
            "registration",
            patient.registration_date,
            "Patient registered",
            "{} - {}".format(
                patient.get_patient_type_display(),
                patient.department.name if patient.department else "Unassigned department",
            ),
        )

        for visit in patient.opd_visits.select_related("doctor")[:50]:
            add(
                "opd",
                visit.visit_date,
                f"OPD consultation - {visit.doctor.name if visit.doctor else 'Doctor'}",
                visit.chief_complaint or "",
                visit.get_status_display(),
            )
        for appointment in patient.appointments.select_related("doctor")[:50]:
            add(
                "appointment",
                appointment.date,
                f"Appointment - {appointment.doctor.name if appointment.doctor else 'Doctor'}",
                appointment.reason or "",
                appointment.get_status_display(),
            )
        for admission in patient.admissions.select_related("doctor")[:20]:
            add(
                "admission",
                admission.admission_date,
                f"Admitted - {admission.ward or 'Ward'} {admission.bed_number or ''}".strip(),
                admission.admission_reason or "",
                admission.get_status_display(),
            )
        for report in patient.lab_reports.select_related("test")[:50]:
            add(
                "laboratory",
                report.report_date or report.sample_collected_at,
                f"Lab report - {report.test.name if report.test else 'Test'}",
                report.result or "",
                report.get_status_display(),
            )
        for study in patient.radiology_studies.all()[:30]:
            add(
                "radiology",
                study.appointment_date,
                f"Radiology - {study.get_scan_type_display()}",
                (study.report or "")[:200],
                study.get_status_display(),
            )
        for prescription in patient.prescriptions.select_related("doctor")[:30]:
            add(
                "prescription",
                prescription.date,
                f"Prescription issued - {prescription.doctor.name if prescription.doctor else ''}".strip(),
                f"{prescription.items.count()} medicine(s)",
                prescription.get_status_display(),
            )
        for document in patient.documents.all()[:50]:
            add(
                "document",
                document.uploaded_at,
                f"Document uploaded - {document.title}",
                document.get_category_display(),
                document.get_ocr_status_display(),
                link=f"/documents/{document.id}",
            )
        for invoice in patient.invoices.all()[:30]:
            add(
                "billing",
                invoice.created_at,
                f"Invoice {invoice.invoice_number}",
                f"Payable {invoice.patient_payable}",
                invoice.get_payment_status_display(),
            )
        for summary in patient.discharge_summaries.all()[:10]:
            add(
                "discharge",
                summary.discharge_date,
                "Discharge summary",
                summary.diagnosis_summary or "",
                summary.get_status_display(),
            )
        for vital in patient.vitals.all()[:20]:
            add(
                "vitals",
                vital.recorded_at,
                "Vitals recorded",
                "BP {} | Pulse {} | SpO2 {}%".format(
                    vital.blood_pressure or "-", vital.pulse_bpm or "-", vital.spo2 or "-"
                ),
                vital.get_status_display(),
            )

        events.sort(key=lambda row: str(row["date"]), reverse=True)
        return Response(
            {"patient_id": patient.patient_id, "count": len(events), "events": events}
        )

    @action(detail=True, methods=["get"])
    def overview(self, request, pk=None):
        """Compact summary used at the top of the patient profile page."""
        patient = self.get_object()
        latest_vitals = patient.vitals.first()
        return Response(
            {
                "patient": PatientSerializer(
                    patient, context={"request": request}
                ).data,
                "latest_vitals": VitalsSerializer(latest_vitals).data
                if latest_vitals
                else None,
                "counts": {
                    "appointments": patient.appointments.count(),
                    "opd_visits": patient.opd_visits.count(),
                    "admissions": patient.admissions.count(),
                    "lab_reports": patient.lab_reports.count(),
                    "radiology": patient.radiology_studies.count(),
                    "prescriptions": patient.prescriptions.count(),
                    "documents": patient.documents.count(),
                    "invoices": patient.invoices.count(),
                    "vitals": patient.vitals.count(),
                },
            }
        )


class VitalsViewSet(BaseViewSet):
    module = "vitals"
    queryset = Vitals.objects.select_related("patient", "recorded_by").all()
    serializer_class = VitalsSerializer
    ordering = ["-recorded_at"]
    apply_patient_scope = True
    patient_lookup = "patient"

    def get_queryset(self):
        queryset = super().get_queryset()
        if patient := self.request.query_params.get("patient"):
            queryset = queryset.filter(patient_id=patient)
        if target := self.request.query_params.get("date"):
            queryset = queryset.filter(recorded_at__date=target)
        return queryset

    @action(detail=False, methods=["get"])
    def latest(self, request):
        """Most recent vitals per patient (used by ward dashboards)."""
        seen = set()
        rows = []
        for vital in self.get_queryset()[:500]:
            if vital.patient_id in seen:
                continue
            seen.add(vital.patient_id)
            rows.append(VitalsSerializer(vital).data)
        return Response({"count": len(rows), "results": rows})


class NurseAssignmentViewSet(BaseViewSet):
    module = "patients"
    queryset = NurseAssignment.objects.select_related(
        "patient", "nurse", "shift"
    ).all()
    serializer_class = NurseAssignmentSerializer
    ordering = ["-assigned_on"]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        if patient := params.get("patient"):
            queryset = queryset.filter(patient_id=patient)
        if nurse := params.get("nurse"):
            queryset = queryset.filter(nurse_id=nurse)
        if params.get("today") == "true":
            from datetime import date

            queryset = queryset.filter(assigned_on=date.today())
        user = self.request.user
        if user.role == "nurse":
            staff = getattr(user, "staff_profile", None)
            if staff is not None:
                queryset = queryset.filter(nurse=staff)
        return queryset
