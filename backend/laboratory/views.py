from datetime import date

from django.db.models import Count
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response

from config.viewsets import BaseReadOnlyViewSet, BaseViewSet

from .models import LabReport, LabTest
from .serializers import LabReportSerializer, LabReportWriteSerializer, LabTestSerializer


class LabTestViewSet(BaseReadOnlyViewSet):
    module = "laboratory"
    queryset = LabTest.objects.all()
    serializer_class = LabTestSerializer
    search_fields = ["name", "code", "category"]
    ordering = ["name"]
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        if category := self.request.query_params.get("category"):
            queryset = queryset.filter(category=category)
        return queryset


class LabReportViewSet(BaseViewSet):
    module = "laboratory"
    queryset = LabReport.objects.select_related("patient", "doctor", "test").all()
    search_fields = ["lab_id", "patient__name", "patient__patient_id", "result"]
    ordering_fields = ["ordered_at", "report_date"]
    ordering = ["-ordered_at"]
    apply_patient_scope = True
    patient_lookup = "patient"

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return LabReportWriteSerializer
        return LabReportSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        if status_value := params.get("status"):
            queryset = queryset.filter(status=status_value)
        if flag := params.get("flag"):
            queryset = queryset.filter(flag=flag)
        if patient := params.get("patient"):
            queryset = queryset.filter(patient_id=patient)
        if doctor := params.get("doctor"):
            queryset = queryset.filter(doctor_id=doctor)
        if category := params.get("category"):
            queryset = queryset.filter(test__category=category)
        if params.get("today") == "true":
            queryset = queryset.filter(ordered_at__date=date.today())
        return queryset

    @action(detail=True, methods=["post"])
    def collect_sample(self, request, pk=None):
        report = self.get_object()
        report.status = LabReport.Status.SAMPLE_COLLECTED
        report.sample_collected_at = timezone.now()
        report.save(update_fields=["status", "sample_collected_at", "updated_at"])
        self._audit("Collected sample for", report)
        return Response(LabReportSerializer(report).data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Attach a result and mark the report completed."""
        report = self.get_object()
        serializer = LabReportWriteSerializer(
            report, data={**request.data, "status": LabReport.Status.COMPLETED}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(report_date=timezone.now(), technician=request.user)
        self._audit("Completed", report)
        return Response(LabReportSerializer(report).data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        queryset = self.get_queryset()
        return Response(
            {
                "total": queryset.count(),
                "ordered": queryset.filter(status=LabReport.Status.ORDERED).count(),
                "sample_collected": queryset.filter(
                    status=LabReport.Status.SAMPLE_COLLECTED
                ).count(),
                "processing": queryset.filter(status=LabReport.Status.PROCESSING).count(),
                "completed": queryset.filter(status=LabReport.Status.COMPLETED).count(),
                "pending": queryset.exclude(
                    status__in=[LabReport.Status.COMPLETED, LabReport.Status.CANCELLED]
                ).count(),
                "critical_flags": queryset.filter(flag=LabReport.Flag.CRITICAL).count(),
                "abnormal": queryset.filter(
                    flag__in=[LabReport.Flag.HIGH, LabReport.Flag.LOW]
                ).count(),
                "today": queryset.filter(ordered_at__date=date.today()).count(),
                "by_category": list(
                    queryset.values("test__category")
                    .annotate(total=Count("id"))
                    .order_by("-total")
                ),
            }
        )
