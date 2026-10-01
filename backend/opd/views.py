from datetime import date

from django.db.models import Count
from rest_framework.decorators import action
from rest_framework.response import Response

from config.viewsets import BaseViewSet

from .models import OPDVisit
from .serializers import OPDVisitSerializer, OPDVisitWriteSerializer


class OPDVisitViewSet(BaseViewSet):
    module = "opd"
    queryset = OPDVisit.objects.select_related("patient", "doctor", "department").all()
    search_fields = [
        "visit_id",
        "patient__name",
        "patient__patient_id",
        "diagnosis",
        "chief_complaint",
    ]
    ordering_fields = ["visit_date", "created_at"]
    ordering = ["-visit_date"]
    apply_patient_scope = True
    patient_lookup = "patient"

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return OPDVisitWriteSerializer
        return OPDVisitSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        if target := params.get("date"):
            queryset = queryset.filter(visit_date=target)
        elif params.get("today") == "true":
            queryset = queryset.filter(visit_date=date.today())
        if status_value := params.get("status"):
            queryset = queryset.filter(status=status_value)
        if doctor := params.get("doctor"):
            queryset = queryset.filter(doctor_id=doctor)
        if department := params.get("department"):
            queryset = queryset.filter(department_id=department)
        if patient := params.get("patient"):
            queryset = queryset.filter(patient_id=patient)
        return queryset

    @action(detail=False, methods=["get"])
    def stats(self, request):
        queryset = self.get_queryset()
        return Response(
            {
                "total": queryset.count(),
                "today": queryset.filter(visit_date=date.today()).count(),
                "waiting": queryset.filter(status=OPDVisit.Status.WAITING).count(),
                "in_consultation": queryset.filter(
                    status=OPDVisit.Status.IN_CONSULTATION
                ).count(),
                "completed": queryset.filter(status=OPDVisit.Status.COMPLETED).count(),
                "follow_ups_due": queryset.filter(
                    follow_up_date__gte=date.today(),
                    follow_up_date__lte=date.today().replace(day=28),
                ).count(),
                "by_department": list(
                    queryset.values("department__name")
                    .annotate(total=Count("id"))
                    .order_by("-total")
                ),
            }
        )
