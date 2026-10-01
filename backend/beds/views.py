from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status as http_status
from rest_framework.decorators import action
from rest_framework.response import Response

from config.viewsets import BaseViewSet
from patients.models import Patient

from .models import Bed, Ward
from .serializers import BedAssignSerializer, BedSerializer, WardSerializer


class WardViewSet(BaseViewSet):
    module = "beds"
    queryset = Ward.objects.select_related("department").prefetch_related("beds").all()
    serializer_class = WardSerializer
    search_fields = ["name", "code", "description"]
    ordering = ["name"]
    pagination_class = None


class BedViewSet(BaseViewSet):
    module = "beds"
    queryset = Bed.objects.select_related(
        "ward", "department", "patient"
    ).all()
    serializer_class = BedSerializer
    search_fields = ["bed_number", "room_number", "patient__name", "patient__patient_id"]
    ordering_fields = ["bed_number", "daily_rate"]
    ordering = ["bed_number"]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        if ward := params.get("ward"):
            queryset = queryset.filter(ward_id=ward)
        if category := params.get("category"):
            queryset = queryset.filter(category=category)
        if status_value := params.get("status"):
            queryset = queryset.filter(status=status_value)
        if department := params.get("department"):
            queryset = queryset.filter(department_id=department)
        if floor := params.get("floor"):
            queryset = queryset.filter(floor=floor)
        if params.get("available") == "true":
            queryset = queryset.filter(status=Bed.Status.AVAILABLE)
        return queryset

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Live occupancy numbers for the bed management dashboard."""
        queryset = Bed.objects.all()
        total = queryset.count()
        occupied = queryset.filter(status=Bed.Status.OCCUPIED).count()
        by_category = []
        for category, label in Bed.Category.choices:
            rows = queryset.filter(category=category)
            category_total = rows.count()
            by_category.append(
                {
                    "category": category,
                    "label": label,
                    "total": category_total,
                    "occupied": rows.filter(status=Bed.Status.OCCUPIED).count(),
                    "available": rows.filter(status=Bed.Status.AVAILABLE).count(),
                    "reserved": rows.filter(status=Bed.Status.RESERVED).count(),
                    "maintenance": rows.filter(
                        status__in=[Bed.Status.MAINTENANCE, Bed.Status.CLEANING]
                    ).count(),
                    "occupancy_rate": round(
                        100 * rows.filter(status=Bed.Status.OCCUPIED).count() / category_total
                    )
                    if category_total
                    else 0,
                }
            )

        icu = queryset.filter(category=Bed.Category.ICU)
        icu_total = icu.count()
        return Response(
            {
                "total": total,
                "occupied": occupied,
                "available": queryset.filter(status=Bed.Status.AVAILABLE).count(),
                "reserved": queryset.filter(status=Bed.Status.RESERVED).count(),
                "maintenance": queryset.filter(
                    status__in=[Bed.Status.MAINTENANCE, Bed.Status.CLEANING]
                ).count(),
                "occupancy_rate": round(100 * occupied / total) if total else 0,
                "icu": {
                    "total": icu_total,
                    "occupied": icu.filter(status=Bed.Status.OCCUPIED).count(),
                    "available": icu.filter(status=Bed.Status.AVAILABLE).count(),
                    "occupancy_rate": round(
                        100 * icu.filter(status=Bed.Status.OCCUPIED).count() / icu_total
                    )
                    if icu_total
                    else 0,
                },
                "by_category": by_category,
                "by_ward": list(
                    Ward.objects.annotate(
                        total=Count("beds"),
                        occupied=Count(
                            "beds", filter=Q(beds__status=Bed.Status.OCCUPIED)
                        ),
                        available=Count(
                            "beds", filter=Q(beds__status=Bed.Status.AVAILABLE)
                        ),
                    ).values("id", "name", "code", "total", "occupied", "available")
                ),
            }
        )

    @action(detail=False, methods=["get"])
    def board(self, request):
        """Visual bed board: every bed grouped by ward."""
        wards = Ward.objects.prefetch_related("beds__patient").all()
        payload = []
        for ward in wards:
            beds = ward.beds.all()
            payload.append(
                {
                    "ward": WardSerializer(ward).data,
                    "beds": BedSerializer(beds, many=True).data,
                }
            )
        unassigned = Bed.objects.filter(ward__isnull=True)
        if unassigned.exists():
            payload.append(
                {
                    "ward": {
                        "id": None,
                        "name": "Unassigned beds",
                        "code": "-",
                        "total_beds": unassigned.count(),
                    },
                    "beds": BedSerializer(unassigned, many=True).data,
                }
            )
        return Response({"wards": payload})

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        """Assign a patient to a bed."""
        bed = self.get_object()
        serializer = BedAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if bed.status == Bed.Status.OCCUPIED and bed.patient_id:
            return Response(
                {
                    "detail": f"Bed {bed.bed_number} is already occupied.",
                    "code": "invalid",
                    "errors": {"bed": "Choose an available bed."},
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        patient = Patient.objects.filter(
            pk=serializer.validated_data["patient"]
        ).first()
        if patient is None:
            return Response(
                {"detail": "Patient not found.", "code": "not_found", "errors": {}},
                status=http_status.HTTP_404_NOT_FOUND,
            )
        bed.patient = patient
        bed.status = Bed.Status.OCCUPIED
        bed.notes = serializer.validated_data.get("notes") or bed.notes
        bed.save(update_fields=["patient", "status", "notes", "updated_at"])
        self._audit("Assigned patient to", bed)
        return Response(BedSerializer(bed).data)

    @action(detail=True, methods=["post"])
    def release(self, request, pk=None):
        """Discharge a patient from a bed and send it for cleaning."""
        bed = self.get_object()
        bed.patient = None
        bed.status = Bed.Status.CLEANING
        bed.last_cleaned_at = timezone.now()
        bed.save(
            update_fields=["patient", "status", "last_cleaned_at", "updated_at"]
        )
        self._audit("Released", bed)
        return Response(BedSerializer(bed).data)

    @action(detail=True, methods=["post"])
    def set_status(self, request, pk=None):
        bed = self.get_object()
        new_status = request.data.get("status")
        if new_status not in dict(Bed.Status.choices):
            return Response(
                {
                    "detail": "Unknown bed status.",
                    "code": "invalid",
                    "errors": {"status": f"Choose one of: {', '.join(dict(Bed.Status.choices))}."},
                },
                status=http_status.HTTP_400_BAD_REQUEST,
            )
        bed.status = new_status
        if new_status == Bed.Status.AVAILABLE:
            bed.patient = None
        bed.save(update_fields=["status", "patient", "updated_at"])
        self._audit("Updated status of", bed)
        return Response(BedSerializer(bed).data)
