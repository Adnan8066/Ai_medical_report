from datetime import date, timedelta

from django.db.models import Count
from rest_framework.decorators import action
from rest_framework.response import Response

from config.viewsets import BaseViewSet

from .models import Appointment
from .serializers import AppointmentSerializer, AppointmentWriteSerializer


class AppointmentViewSet(BaseViewSet):
    module = "appointments"
    queryset = Appointment.objects.select_related(
        "patient", "doctor", "doctor__department", "department"
    ).all()
    search_fields = ["appointment_id", "patient__name", "patient__patient_id", "reason"]
    ordering_fields = ["date", "time", "created_at"]
    ordering = ["-date", "time"]
    apply_patient_scope = True
    patient_lookup = "patient"

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return AppointmentWriteSerializer
        return AppointmentSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        if target := params.get("date"):
            queryset = queryset.filter(date=target)
        elif params.get("today") == "true":
            queryset = queryset.filter(date=date.today())
        if week := params.get("week"):
            start = date.today() - timedelta(days=date.today().weekday())
            queryset = queryset.filter(
                date__gte=start, date__lte=start + timedelta(days=int(week) - 1)
            )
        if status_value := params.get("status"):
            queryset = queryset.filter(status=status_value)
        if doctor := params.get("doctor"):
            queryset = queryset.filter(doctor_id=doctor)
        if department := params.get("department"):
            queryset = queryset.filter(department_id=department)
        if patient := params.get("patient"):
            queryset = queryset.filter(patient_id=patient)
        if appointment_type := params.get("appointment_type"):
            queryset = queryset.filter(appointment_type=appointment_type)
        return queryset

    @action(detail=False, methods=["get"])
    def today(self, request):
        """Today's appointment board."""
        queryset = self.get_queryset().filter(date=date.today())
        return Response(
            {
                "date": date.today(),
                "count": queryset.count(),
                "results": AppointmentSerializer(queryset, many=True).data,
            }
        )

    @action(detail=False, methods=["get"])
    def upcoming(self, request):
        days = int(request.query_params.get("days", 7))
        start = date.today()
        queryset = self.get_queryset().filter(
            date__gte=start, date__lte=start + timedelta(days=days)
        )
        return Response(AppointmentSerializer(queryset[:50], many=True).data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        queryset = self.get_queryset()
        today = queryset.filter(date=date.today())
        return Response(
            {
                "total": queryset.count(),
                "today": today.count(),
                "scheduled": queryset.filter(status=Appointment.Status.SCHEDULED).count(),
                "confirmed": queryset.filter(status=Appointment.Status.CONFIRMED).count(),
                "completed": queryset.filter(status=Appointment.Status.COMPLETED).count(),
                "cancelled": queryset.filter(status=Appointment.Status.CANCELLED).count(),
                "no_show": queryset.filter(status=Appointment.Status.NO_SHOW).count(),
                "by_department": list(
                    today.values("department__name")
                    .annotate(total=Count("id"))
                    .order_by("-total")
                ),
            }
        )

    @action(detail=True, methods=["post"])
    def set_status(self, request, pk=None):
        """Move an appointment through its lifecycle."""
        appointment = self.get_object()
        new_status = request.data.get("status")
        valid = dict(Appointment.Status.choices)
        if new_status not in valid:
            return Response(
                {
                    "detail": "Unknown appointment status.",
                    "code": "invalid",
                    "errors": {"status": f"Choose one of: {', '.join(valid)}."},
                },
                status=400,
            )
        appointment.status = new_status
        appointment.save(update_fields=["status", "updated_at"])
        self._audit("Updated status of", appointment)
        return Response(AppointmentSerializer(appointment).data)
