from datetime import date

from django.db.models import Count
from rest_framework.decorators import action
from rest_framework.response import Response

from config.viewsets import BaseViewSet

from .models import Surgery
from .serializers import SurgerySerializer, SurgeryWriteSerializer


class SurgeryViewSet(BaseViewSet):
    module = "surgery"
    queryset = Surgery.objects.select_related(
        "patient", "surgeon", "anesthetist", "department"
    ).prefetch_related("nurses")
    search_fields = ["surgery_id", "patient__name", "patient__patient_id", "surgery_name", "ot_room"]
    ordering_fields = ["date", "start_time"]
    ordering = ["-date", "start_time"]
    apply_patient_scope = True
    patient_lookup = "patient"

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return SurgeryWriteSerializer
        return SurgerySerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        if status_value := params.get("status"):
            queryset = queryset.filter(status=status_value)
        if target := params.get("date"):
            queryset = queryset.filter(date=target)
        elif params.get("today") == "true":
            queryset = queryset.filter(date=date.today())
        if ot_room := params.get("ot_room"):
            queryset = queryset.filter(ot_room=ot_room)
        if patient := params.get("patient"):
            queryset = queryset.filter(patient_id=patient)
        if surgeon := params.get("surgeon"):
            queryset = queryset.filter(surgeon_id=surgeon)
        return queryset

    @action(detail=False, methods=["get"])
    def schedule(self, request):
        """Theatre schedule for a given day."""
        target = request.query_params.get("date") or date.today().isoformat()
        surgeries = self.get_queryset().filter(date=target).order_by("ot_room", "start_time")
        rooms = {}
        for surgery in surgeries:
            rooms.setdefault(surgery.ot_room, []).append(
                SurgerySerializer(surgery).data
            )
        return Response({"date": target, "rooms": rooms, "total": surgeries.count()})

    @action(detail=False, methods=["get"])
    def stats(self, request):
        queryset = self.get_queryset()
        today = queryset.filter(date=date.today())
        return Response(
            {
                "total": queryset.count(),
                "today": today.count(),
                "scheduled": queryset.filter(status=Surgery.Status.SCHEDULED).count(),
                "preparing": queryset.filter(status=Surgery.Status.PREPARING).count(),
                "in_progress": queryset.filter(status=Surgery.Status.IN_PROGRESS).count(),
                "completed": queryset.filter(status=Surgery.Status.COMPLETED).count(),
                "cancelled": queryset.filter(status=Surgery.Status.CANCELLED).count(),
                "by_department": list(
                    queryset.values("department__name")
                    .annotate(total=Count("id"))
                    .order_by("-total")
                ),
                "ot_rooms": list(
                    queryset.values("ot_room").annotate(total=Count("id")).order_by("ot_room")
                ),
            }
        )
