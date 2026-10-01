from datetime import date

from django.db.models import Count, Q
from rest_framework.decorators import action
from rest_framework.response import Response

from config.viewsets import BaseViewSet, BaseReadOnlyViewSet

from .models import Doctor
from .serializers import DoctorListSerializer, DoctorSerializer


class DoctorViewSet(BaseViewSet):
    module = "doctors"
    queryset = Doctor.objects.select_related("department").all()
    search_fields = ["name", "doctor_id", "specialization", "qualification", "room_number"]
    ordering_fields = ["name", "experience_years", "consultation_fee", "joining_date"]
    ordering = ["name"]

    def get_serializer_class(self):
        if self.action == "list":
            return DoctorListSerializer
        return DoctorSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        if department := params.get("department"):
            queryset = queryset.filter(department_id=department)
        if params.get("is_hod") in {"true", "false"}:
            queryset = queryset.filter(is_hod=params["is_hod"] == "true")
        if availability := params.get("availability"):
            queryset = queryset.filter(availability=availability)
        if status := params.get("status"):
            queryset = queryset.filter(status=status)
        if designation := params.get("designation"):
            queryset = queryset.filter(designation=designation)
        if self.action == "list":
            queryset = queryset.annotate(patient_total=Count("patients", distinct=True))
        return queryset

    @action(detail=False, methods=["get"])
    def hods(self, request):
        """Every Head of Department across the hospital."""
        queryset = self.get_queryset().filter(is_hod=True).select_related("department")
        return Response(DoctorListSerializer(queryset, many=True).data)

    @action(detail=False, methods=["get"])
    def directory(self, request):
        """Grouped directory used by the department explorer screen."""
        doctors = self.get_queryset().filter(status=Doctor.Status.ACTIVE)
        grouped = {}
        for doctor in doctors:
            grouped.setdefault(
                doctor.department.name if doctor.department else "Unassigned", []
            ).append(DoctorListSerializer(doctor).data)
        return Response({"departments": grouped, "total": len(doctors)})

    @action(detail=True, methods=["get"])
    def schedule(self, request, pk=None):
        doctor = self.get_object()
        upcoming = (
            doctor.appointments.filter(date__gte=date.today())
            .order_by("date", "time")
            .values("appointment_id", "date", "time", "status", "patient__name")[:10]
        )
        return Response(
            {
                "doctor": DoctorSerializer(doctor).data,
                "opd_schedule": doctor.opd_schedule,
                "available_days": doctor.available_days,
                "upcoming_appointments": list(upcoming),
            }
        )

    @action(detail=True, methods=["get"])
    def patients(self, request, pk=None):
        doctor = self.get_object()
        from patients.serializers import PatientListSerializer

        queryset = doctor.patients.select_related("department").all()
        return Response(PatientListSerializer(queryset, many=True).data)
