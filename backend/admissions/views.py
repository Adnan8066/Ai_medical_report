from datetime import date

from django.db import transaction
from django.db.models import Count
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response

from config.viewsets import BaseViewSet
from patients.models import Patient

from .models import Admission, DischargeSummary
from .serializers import (
    AdmissionSerializer,
    AdmissionWriteSerializer,
    DischargeSummarySerializer,
)


class AdmissionViewSet(BaseViewSet):
    module = "admissions"
    queryset = Admission.objects.select_related(
        "patient", "doctor", "attending_doctor", "department", "ward", "bed", "nurse"
    ).all()
    search_fields = [
        "admission_id",
        "patient__name",
        "patient__patient_id",
        "diagnosis",
        "admission_reason",
    ]
    ordering_fields = ["admission_date", "expected_discharge_date"]
    ordering = ["-admission_date"]
    apply_patient_scope = True
    patient_lookup = "patient"

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return AdmissionWriteSerializer
        return AdmissionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        if status_value := params.get("status"):
            queryset = queryset.filter(status=status_value)
        if department := params.get("department"):
            queryset = queryset.filter(department_id=department)
        if doctor := params.get("doctor"):
            queryset = queryset.filter(doctor_id=doctor)
        if patient := params.get("patient"):
            queryset = queryset.filter(patient_id=patient)
        if params.get("current") == "true":
            queryset = queryset.filter(
                status__in=[
                    Admission.Status.ADMITTED,
                    Admission.Status.UNDER_TREATMENT,
                    Admission.Status.READY_FOR_DISCHARGE,
                ]
            )
        if params.get("today") == "true":
            queryset = queryset.filter(admission_date__date=date.today())
        return queryset

    def perform_create(self, serializer):
        """Admitting a patient occupies the bed and updates the patient record."""
        with transaction.atomic():
            admission = serializer.save()
            if admission.bed_id:
                bed = admission.bed
                bed.status = "occupied"
                bed.patient = admission.patient
                bed.save(update_fields=["status", "patient", "updated_at"])
            patient = admission.patient
            patient.admission_status = Patient.AdmissionStatus.ADMITTED
            patient.current_status = Patient.Status.ADMITTED
            patient.patient_type = Patient.PatientType.INPATIENT
            patient.save(
                update_fields=["admission_status", "current_status", "patient_type", "updated_at"]
            )
            self._audit("Admitted", admission)
        return admission

    def perform_update(self, serializer):
        with transaction.atomic():
            admission = serializer.save()
            if admission.status == Admission.Status.DISCHARGED:
                self._release_resources(admission)
            self._audit("Updated", admission)
        return admission

    @staticmethod
    def _release_resources(admission):
        if admission.bed_id:
            bed = admission.bed
            bed.patient = None
            bed.status = "cleaning"
            bed.last_cleaned_at = timezone.now()
            bed.save(update_fields=["patient", "status", "last_cleaned_at", "updated_at"])
        patient = admission.patient
        patient.admission_status = Patient.AdmissionStatus.DISCHARGED
        patient.current_status = Patient.Status.DISCHARGED
        patient.save(update_fields=["admission_status", "current_status", "updated_at"])

    @action(detail=True, methods=["post"])
    def discharge(self, request, pk=None):
        """Close the admission, release the bed and update the patient record."""
        admission = self.get_object()
        if admission.status == Admission.Status.DISCHARGED:
            return Response(
                {
                    "detail": "This admission is already discharged.",
                    "code": "invalid",
                    "errors": {},
                },
                status=400,
            )
        with transaction.atomic():
            admission.status = Admission.Status.DISCHARGED
            admission.discharge_date = timezone.now()
            admission.save(update_fields=["status", "discharge_date", "updated_at"])
            self._release_resources(admission)
            self._audit("Discharged", admission)
        return Response(AdmissionSerializer(admission).data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        queryset = self.get_queryset()
        current = queryset.filter(
            status__in=[
                Admission.Status.ADMITTED,
                Admission.Status.UNDER_TREATMENT,
                Admission.Status.READY_FOR_DISCHARGE,
            ]
        )
        return Response(
            {
                "total": queryset.count(),
                "current_inpatients": current.count(),
                "admitted_today": queryset.filter(
                    admission_date__date=date.today()
                ).count(),
                "ready_for_discharge": queryset.filter(
                    status=Admission.Status.READY_FOR_DISCHARGE
                ).count(),
                "discharged_today": queryset.filter(
                    discharge_date__date=date.today()
                ).count(),
                "average_stay_days": round(
                    sum(item.length_of_stay for item in queryset[:200])
                    / max(1, len(queryset[:200])),
                    1,
                ),
                "by_department": list(
                    current.values("department__name")
                    .annotate(total=Count("id"))
                    .order_by("-total")
                ),
            }
        )


class DischargeSummaryViewSet(BaseViewSet):
    module = "admissions"
    queryset = DischargeSummary.objects.select_related(
        "patient", "doctor", "admission", "final_bill"
    ).all()
    serializer_class = DischargeSummarySerializer
    search_fields = ["discharge_id", "patient__name", "patient__patient_id"]
    ordering = ["-created_at"]
    apply_patient_scope = True
    patient_lookup = "patient"

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        if patient := params.get("patient"):
            queryset = queryset.filter(patient_id=patient)
        if status_value := params.get("status"):
            queryset = queryset.filter(status=status_value)
        return queryset

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """Doctor approval step of the discharge workflow."""
        summary = self.get_object()
        summary.doctor_approved = True
        summary.status = DischargeSummary.Status.APPROVED
        summary.approved_by = request.user
        summary.approved_at = timezone.now()
        summary.save(
            update_fields=[
                "doctor_approved",
                "status",
                "approved_by",
                "approved_at",
                "updated_at",
            ]
        )
        if summary.admission and summary.admission.status != Admission.Status.DISCHARGED:
            summary.admission.status = Admission.Status.READY_FOR_DISCHARGE
            summary.admission.save(update_fields=["status", "updated_at"])
        self._audit("Approved", summary)
        return Response(DischargeSummarySerializer(summary).data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Final step: mark the patient discharged and free the bed."""
        summary = self.get_object()
        if not summary.doctor_approved:
            return Response(
                {
                    "detail": "The discharge summary must be approved by the doctor first.",
                    "code": "invalid",
                    "errors": {"doctor_approved": "Approval is still pending."},
                },
                status=400,
            )
        with transaction.atomic():
            summary.status = DischargeSummary.Status.COMPLETED
            if not summary.discharge_date:
                summary.discharge_date = timezone.now()
            summary.save(update_fields=["status", "discharge_date", "updated_at"])
            admission = summary.admission
            if admission is not None and admission.status != Admission.Status.DISCHARGED:
                admission.status = Admission.Status.DISCHARGED
                admission.discharge_date = summary.discharge_date
                admission.save(update_fields=["status", "discharge_date", "updated_at"])
                AdmissionViewSet._release_resources(admission)
            self._audit("Completed", summary)
        return Response(DischargeSummarySerializer(summary).data)
