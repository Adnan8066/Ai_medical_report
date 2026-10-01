from datetime import date, timedelta

from django.db.models import Count
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response

from config.viewsets import BaseViewSet

from .models import EmergencyVisit
from .serializers import EmergencyVisitSerializer, EmergencyVisitWriteSerializer


class EmergencyVisitViewSet(BaseViewSet):
    module = "emergency"
    queryset = EmergencyVisit.objects.select_related(
        "patient", "assigned_doctor", "assigned_nurse", "bed"
    ).all()
    search_fields = ["case_id", "patient__name", "patient__patient_id", "chief_complaint"]
    ordering_fields = ["arrival_time", "priority"]
    ordering = ["-arrival_time"]
    apply_patient_scope = True
    patient_lookup = "patient"

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return EmergencyVisitWriteSerializer
        return EmergencyVisitSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        if priority := params.get("priority"):
            queryset = queryset.filter(priority=priority)
        if status_value := params.get("status"):
            queryset = queryset.filter(status=status_value)
        if params.get("today") == "true":
            queryset = queryset.filter(arrival_time__date=date.today())
        elif target := params.get("date"):
            queryset = queryset.filter(arrival_time__date=target)
        if params.get("active") == "true":
            queryset = queryset.exclude(
                status__in=[
                    EmergencyVisit.Status.DISCHARGED,
                    EmergencyVisit.Status.REFERRED,
                    EmergencyVisit.Status.TRANSFERRED,
                ]
            )
        if doctor := params.get("doctor"):
            queryset = queryset.filter(assigned_doctor_id=doctor)
        return queryset

    @action(detail=False, methods=["get"])
    def board(self, request):
        """Live emergency department board grouped by triage priority."""
        active = self.get_queryset().filter(
            arrival_time__date__gte=date.today() - timedelta(days=1)
        ).exclude(
            status__in=[
                EmergencyVisit.Status.DISCHARGED,
                EmergencyVisit.Status.REFERRED,
                EmergencyVisit.Status.TRANSFERRED,
            ]
        )
        by_priority = {}
        for priority, label in EmergencyVisit.Priority.choices:
            rows = [case for case in active if case.priority == priority]
            by_priority[priority] = {
                "label": label,
                "count": len(rows),
                "cases": EmergencyVisitSerializer(rows, many=True).data,
            }

        waiting = [
            case.waiting_minutes for case in active if case.status == EmergencyVisit.Status.WAITING
        ]
        return Response(
            {
                "generated_at": timezone.now(),
                "active_count": active.count(),
                "average_wait_minutes": round(sum(waiting) / len(waiting)) if waiting else 0,
                "longest_wait_minutes": max(waiting) if waiting else 0,
                "by_priority": by_priority,
            }
        )

    @action(detail=False, methods=["get"])
    def stats(self, request):
        queryset = self.get_queryset()
        today = queryset.filter(arrival_time__date=date.today())
        return Response(
            {
                "total": queryset.count(),
                "today": today.count(),
                "critical": today.filter(priority=EmergencyVisit.Priority.CRITICAL).count(),
                "high": today.filter(priority=EmergencyVisit.Priority.HIGH).count(),
                "medium": today.filter(priority=EmergencyVisit.Priority.MEDIUM).count(),
                "low": today.filter(priority=EmergencyVisit.Priority.LOW).count(),
                "waiting": today.filter(status=EmergencyVisit.Status.WAITING).count(),
                "in_treatment": today.filter(
                    status=EmergencyVisit.Status.IN_TREATMENT
                ).count(),
                "admitted": today.filter(status=EmergencyVisit.Status.ADMITTED).count(),
                "trend": list(
                    EmergencyVisit.objects.filter(
                        arrival_time__date__gte=date.today() - timedelta(days=14)
                    )
                    .values("arrival_time__date")
                    .annotate(total=Count("id"))
                    .order_by("arrival_time__date")
                ),
            }
        )
