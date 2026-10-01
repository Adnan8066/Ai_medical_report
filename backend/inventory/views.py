from datetime import date, timedelta

from django.db import transaction
from django.db.models import Count, F, Sum
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response

from config.viewsets import BaseViewSet

from .models import InventoryItem, PurchaseOrder, StockMovement, Supplier
from .serializers import (
    InventoryItemSerializer,
    PurchaseOrderSerializer,
    StockMovementSerializer,
    SupplierSerializer,
)


class SupplierViewSet(BaseViewSet):
    module = "inventory"
    queryset = Supplier.objects.prefetch_related("items").all()
    serializer_class = SupplierSerializer
    search_fields = ["name", "code", "contact_person", "phone", "email"]
    ordering = ["name"]


class InventoryItemViewSet(BaseViewSet):
    module = "inventory"
    queryset = InventoryItem.objects.select_related("supplier").all()
    serializer_class = InventoryItemSerializer
    search_fields = ["name", "item_code", "description", "batch_number", "location"]
    ordering_fields = ["name", "stock", "expiry_date"]
    ordering = ["name"]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        if category := params.get("category"):
            queryset = queryset.filter(category=category)
        if status_value := params.get("status"):
            queryset = queryset.filter(status=status_value)
        if supplier := params.get("supplier"):
            queryset = queryset.filter(supplier_id=supplier)
        if params.get("low_stock") == "true":
            queryset = queryset.filter(stock__lte=F("reorder_level"))
        return queryset

    @action(detail=False, methods=["get"])
    def stats(self, request):
        queryset = InventoryItem.objects.all()
        horizon = date.today() + timedelta(days=60)
        return Response(
            {
                "total_items": queryset.count(),
                "low_stock": queryset.filter(
                    stock__lte=F("reorder_level"), stock__gt=0
                ).count(),
                "out_of_stock": queryset.filter(stock=0).count(),
                "expiring_soon": queryset.filter(
                    expiry_date__isnull=False,
                    expiry_date__gte=date.today(),
                    expiry_date__lte=horizon,
                ).count(),
                "total_stock_value": queryset.aggregate(
                    value=Sum(F("stock") * F("unit_price"))
                )["value"]
                or 0,
                "by_category": list(
                    queryset.values("category")
                    .annotate(total=Count("id"), value=Sum(F("stock") * F("unit_price")))
                    .order_by("-total")
                ),
                "open_purchase_orders": PurchaseOrder.objects.exclude(
                    status__in=[
                        PurchaseOrder.Status.RECEIVED,
                        PurchaseOrder.Status.CANCELLED,
                    ]
                ).count(),
            }
        )

    @action(detail=True, methods=["post"])
    def adjust_stock(self, request, pk=None):
        """Apply a stock movement and keep the running balance in sync."""
        item = self.get_object()
        movement_type = request.data.get("movement_type", StockMovement.MovementType.IN)
        if movement_type not in dict(StockMovement.MovementType.choices):
            return Response(
                {
                    "detail": "Unknown movement type.",
                    "code": "invalid",
                    "errors": {
                        "movement_type": f"Choose one of: {', '.join(dict(StockMovement.MovementType.choices))}."
                    },
                },
                status=400,
            )
        try:
            quantity = int(request.data.get("quantity", 0))
        except (TypeError, ValueError):
            return Response(
                {
                    "detail": "Quantity must be a whole number.",
                    "code": "invalid",
                    "errors": {"quantity": "Enter a whole number."},
                },
                status=400,
            )
        if quantity == 0:
            return Response(
                {
                    "detail": "Enter a quantity other than zero.",
                    "code": "invalid",
                    "errors": {"quantity": "Quantity must not be zero."},
                },
                status=400,
            )

        signed = -abs(quantity) if movement_type in {
            StockMovement.MovementType.OUT,
            StockMovement.MovementType.DISPOSAL,
        } else quantity

        with transaction.atomic():
            item = InventoryItem.objects.select_for_update().get(pk=item.pk)
            if item.stock + signed < 0:
                return Response(
                    {
                        "detail": "Stock cannot become negative.",
                        "code": "invalid",
                        "errors": {"quantity": f"Only {item.stock} units are in stock."},
                    },
                    status=400,
                )
            item.stock += signed
            if signed > 0:
                item.last_restocked_at = timezone.now()
            item.status = item.compute_status()
            item.save(update_fields=["stock", "status", "last_restocked_at", "updated_at"])
            movement = StockMovement.objects.create(
                item=item,
                movement_type=movement_type,
                quantity=signed,
                balance_after=item.stock,
                reason=request.data.get("reason", ""),
                reference=request.data.get("reference", ""),
                performed_by=request.user,
            )
            self._audit("Recorded stock movement for", item)
        return Response(
            {
                "item": InventoryItemSerializer(item).data,
                "movement": StockMovementSerializer(movement).data,
            }
        )

    @action(detail=True, methods=["get"])
    def movements(self, request, pk=None):
        item = self.get_object()
        movements = item.movements.all()[:100]
        return Response(StockMovementSerializer(movements, many=True).data)


class PurchaseOrderViewSet(BaseViewSet):
    module = "inventory"
    queryset = PurchaseOrder.objects.select_related("supplier").prefetch_related("items")
    serializer_class = PurchaseOrderSerializer
    search_fields = ["po_number", "supplier__name", "notes"]
    ordering = ["-order_date"]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        if status_value := params.get("status"):
            queryset = queryset.filter(status=status_value)
        if supplier := params.get("supplier"):
            queryset = queryset.filter(supplier_id=supplier)
        return queryset

    @action(detail=True, methods=["post"])
    def receive(self, request, pk=None):
        """Receive ordered goods into stock."""
        order = self.get_object()
        with transaction.atomic():
            for line in order.items.select_related("item"):
                if line.item is None:
                    continue
                outstanding = line.quantity - line.received_quantity
                if outstanding <= 0:
                    continue
                item = InventoryItem.objects.select_for_update().get(pk=line.item.pk)
                item.stock += outstanding
                item.last_restocked_at = timezone.now()
                item.status = item.compute_status()
                item.save(
                    update_fields=["stock", "status", "last_restocked_at", "updated_at"]
                )
                line.received_quantity = line.quantity
                line.save(update_fields=["received_quantity"])
                StockMovement.objects.create(
                    item=item,
                    movement_type=StockMovement.MovementType.IN,
                    quantity=outstanding,
                    balance_after=item.stock,
                    reason=f"Received against {order.po_number}",
                    reference=order.po_number,
                    performed_by=request.user,
                )
            order.status = PurchaseOrder.Status.RECEIVED
            order.save(update_fields=["status"])
            self._audit("Received purchase order", order)
        return Response(PurchaseOrderSerializer(order).data)
