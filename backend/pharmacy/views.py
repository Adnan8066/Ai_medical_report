from datetime import date, timedelta

from django.db import transaction
from django.db.models import Count, F, Sum
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response

from config.viewsets import BaseViewSet

from .models import Medicine, Prescription, PrescriptionItem
from .serializers import (
    MedicineSerializer,
    MedicineWriteSerializer,
    PrescriptionSerializer,
    PrescriptionWriteSerializer,
)


class MedicineViewSet(BaseViewSet):
    module = "pharmacy"
    queryset = Medicine.objects.select_related("supplier").all()
    search_fields = ["name", "generic_name", "medicine_id", "manufacturer", "batch_number"]
    ordering_fields = ["name", "stock", "expiry_date", "price"]
    ordering = ["name"]

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return MedicineWriteSerializer
        return MedicineSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        if category := params.get("category"):
            queryset = queryset.filter(category=category)
        if status_value := params.get("status"):
            queryset = queryset.filter(status=status_value)
        if params.get("low_stock") == "true":
            queryset = queryset.filter(stock__lte=F("reorder_level"))
        if params.get("expiring") == "true":
            horizon = date.today() + timedelta(days=90)
            queryset = queryset.filter(
                expiry_date__isnull=False, expiry_date__lte=horizon
            )
        return queryset

    @action(detail=False, methods=["get"])
    def stats(self, request):
        queryset = Medicine.objects.all()
        horizon = date.today() + timedelta(days=90)
        return Response(
            {
                "total_items": queryset.count(),
                "available": queryset.filter(status=Medicine.Status.AVAILABLE).count(),
                "low_stock": queryset.filter(
                    status__in=[Medicine.Status.LOW_STOCK, Medicine.Status.OUT_OF_STOCK]
                ).count(),
                "out_of_stock": queryset.filter(
                    status=Medicine.Status.OUT_OF_STOCK
                ).count(),
                "expiring_soon": queryset.filter(
                    expiry_date__isnull=False,
                    expiry_date__gte=date.today(),
                    expiry_date__lte=horizon,
                ).count(),
                "expired": queryset.filter(expiry_date__lt=date.today()).count(),
                "stock_value": queryset.aggregate(
                    value=Sum(F("stock") * F("cost_price"))
                )["value"]
                or 0,
                "by_category": list(
                    queryset.values("category").annotate(total=Count("id")).order_by("-total")
                ),
            }
        )

    @action(detail=True, methods=["post"])
    def adjust_stock(self, request, pk=None):
        """Apply a stock in/out movement and refresh the derived status."""
        medicine = self.get_object()
        try:
            delta = int(request.data.get("quantity", 0))
        except (TypeError, ValueError):
            return Response(
                {
                    "detail": "Quantity must be a whole number.",
                    "code": "invalid",
                    "errors": {"quantity": "Enter a positive or negative whole number."},
                },
                status=400,
            )
        if medicine.stock + delta < 0:
            return Response(
                {
                    "detail": "Stock cannot become negative.",
                    "code": "invalid",
                    "errors": {"quantity": f"Only {medicine.stock} units are in stock."},
                },
                status=400,
            )
        medicine.stock += delta
        medicine.status = medicine.compute_status()
        medicine.save(update_fields=["stock", "status", "updated_at"])
        self._audit("Adjusted stock for", medicine)
        return Response(MedicineSerializer(medicine).data)


class PrescriptionViewSet(BaseViewSet):
    module = "prescriptions"
    queryset = Prescription.objects.select_related("patient", "doctor").prefetch_related(
        "items__medicine"
    )
    search_fields = ["prescription_id", "patient__name", "patient__patient_id"]
    ordering = ["-date"]
    apply_patient_scope = True
    patient_lookup = "patient"

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return PrescriptionWriteSerializer
        return PrescriptionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        if patient := params.get("patient"):
            queryset = queryset.filter(patient_id=patient)
        if status_value := params.get("status"):
            queryset = queryset.filter(status=status_value)
        if doctor := params.get("doctor"):
            queryset = queryset.filter(doctor_id=doctor)
        return queryset

    @action(detail=True, methods=["post"])
    def dispense(self, request, pk=None):
        """
        Dispense every pending line on the prescription.

        Stock is decremented atomically; if any line lacks stock the whole
        operation is rejected so inventory never goes negative.
        """
        prescription = self.get_object()
        items = prescription.items.select_related("medicine").all()
        with transaction.atomic():
            for item in items:
                if item.dispensed or item.medicine is None:
                    continue
                medicine = Medicine.objects.select_for_update().get(pk=item.medicine.pk)
                if medicine.stock < item.quantity:
                    return Response(
                        {
                            "detail": f"Not enough stock of {medicine.name}.",
                            "code": "invalid",
                            "errors": {
                                "items": (
                                    f"{medicine.name}: {medicine.stock} available, "
                                    f"{item.quantity} required."
                                )
                            },
                        },
                        status=400,
                    )
                medicine.stock -= item.quantity
                medicine.status = medicine.compute_status()
                medicine.save(update_fields=["stock", "status", "updated_at"])
                item.dispensed = True
                item.save(update_fields=["dispensed"])

            prescription.status = Prescription.Status.DISPENSED
            prescription.dispensed_by = request.user
            prescription.dispensed_at = timezone.now()
            prescription.save(
                update_fields=["status", "dispensed_by", "dispensed_at"]
            )
            self._audit("Dispensed", prescription)
        return Response(PrescriptionSerializer(prescription).data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        queryset = self.get_queryset()
        return Response(
            {
                "total": queryset.count(),
                "pending": queryset.filter(status=Prescription.Status.PENDING).count(),
                "dispensed": queryset.filter(status=Prescription.Status.DISPENSED).count(),
                "today": queryset.filter(date=date.today()).count(),
                "items_pending": PrescriptionItem.objects.filter(dispensed=False).count(),
            }
        )
