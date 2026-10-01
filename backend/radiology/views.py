from datetime import date

from django.db.models import Count
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response

from config.viewsets import BaseViewSet

from .models import RadiologyReport
from .serializers import RadiologyReportSerializer, RadiologyReportWriteSerializer


class RadiologyReportViewSet(BaseViewSet):
    module = "radiology"
    queryset = RadiologyReport.objects.select_related("patient", "doctor").all()
    search_fields = [
        "scan_id",
        "patient__name",
        "patient__patient_id",
        "body_part",
        "impression",
    ]
    ordering_fields = ["appointment_date", "created_at"]
    ordering = ["-appointment_date", "-created_at"]
    apply_patient_scope = True
    patient_lookup = "patient"

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return RadiologyReportWriteSerializer
        return RadiologyReportSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        if scan_type := params.get("scan_type"):
            queryset = queryset.filter(scan_type=scan_type)
        if status_value := params.get("status"):
            queryset = queryset.filter(status=status_value)
        if patient := params.get("patient"):
            queryset = queryset.filter(patient_id=patient)
        if doctor := params.get("doctor"):
            queryset = queryset.filter(doctor_id=doctor)
        if params.get("today") == "true":
            queryset = queryset.filter(appointment_date__date=date.today())
        return queryset

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        report = self.get_object()
        serializer = RadiologyReportWriteSerializer(
            report,
            data={**request.data, "status": RadiologyReport.Status.COMPLETED},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(report_date=timezone.now(), radiologist=request.user)
        self._audit("Completed", report)
        return Response(RadiologyReportSerializer(report).data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        queryset = self.get_queryset()
        return Response(
            {
                "total": queryset.count(),
                "ordered": queryset.filter(status=RadiologyReport.Status.ORDERED).count(),
                "scheduled": queryset.filter(status=RadiologyReport.Status.SCHEDULED).count(),
                "in_progress": queryset.filter(
                    status=RadiologyReport.Status.IN_PROGRESS
                ).count(),
                "completed": queryset.filter(
                    status=RadiologyReport.Status.COMPLETED
                ).count(),
                "today": queryset.filter(appointment_date__date=date.today()).count(),
                "by_scan_type": list(
                    queryset.values("scan_type")
                    .annotate(total=Count("id"))
                    .order_by("-total")
                ),
            }
        )
