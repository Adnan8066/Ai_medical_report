from datetime import date
from decimal import Decimal

from django.db.models import Count, Sum
from rest_framework.decorators import action
from rest_framework.response import Response

from config.viewsets import BaseViewSet

from .models import Invoice
from .serializers import InvoiceSerializer, InvoiceWriteSerializer


class InvoiceViewSet(BaseViewSet):
    module = "billing"
    queryset = Invoice.objects.select_related("patient", "doctor", "admission").prefetch_related(
        "items"
    )
    search_fields = ["invoice_number", "patient__name", "patient__patient_id"]
    ordering_fields = ["date", "patient_payable", "created_at"]
    ordering = ["-date", "-created_at"]
    apply_patient_scope = True
    patient_lookup = "patient"

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return InvoiceWriteSerializer
        return InvoiceSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        if status_value := params.get("status"):
            queryset = queryset.filter(payment_status=status_value)
        if patient := params.get("patient"):
            queryset = queryset.filter(patient_id=patient)
        if service := params.get("service_type"):
            queryset = queryset.filter(items__service_type=service)
        if params.get("today") == "true":
            queryset = queryset.filter(date=date.today())
        if start := params.get("date_from"):
            queryset = queryset.filter(date__gte=start)
        if end := params.get("date_to"):
            queryset = queryset.filter(date__lte=end)
        return queryset.distinct()

    @action(detail=True, methods=["post"])
    def record_payment(self, request, pk=None):
        """Record a (possibly partial) payment against the invoice."""
        invoice = self.get_object()
        try:
            amount = Decimal(str(request.data.get("amount", "0")))
        except Exception:
            return Response(
                {
                    "detail": "Enter a valid payment amount.",
                    "code": "invalid",
                    "errors": {"amount": "Use a number such as 1500.00."},
                },
                status=400,
            )
        if amount <= 0:
            return Response(
                {
                    "detail": "The payment amount must be greater than zero.",
                    "code": "invalid",
                    "errors": {"amount": "Enter an amount greater than zero."},
                },
                status=400,
            )
        invoice.paid_amount = (invoice.paid_amount or Decimal("0")) + amount
        method = request.data.get("payment_method")
        if method in dict(Invoice.PaymentMethod.choices):
            invoice.payment_method = method
        invoice._sync_payment_status()
        invoice.save(
            update_fields=["paid_amount", "payment_method", "payment_status", "updated_at"]
        )
        self._audit("Recorded payment for", invoice)
        return Response(InvoiceSerializer(invoice).data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        queryset = self.get_queryset()
        paid = queryset.filter(payment_status=Invoice.PaymentStatus.PAID)
        pending = queryset.exclude(
            payment_status__in=[Invoice.PaymentStatus.PAID, Invoice.PaymentStatus.CANCELLED]
        )
        revenue_trend = list(
            queryset.values("date")
            .annotate(total=Sum("patient_payable"), invoices=Count("id"))
            .order_by("date")[:60]
        )
        return Response(
            {
                "total_invoices": queryset.count(),
                "paid": paid.count(),
                "pending": queryset.filter(
                    payment_status=Invoice.PaymentStatus.PENDING
                ).count(),
                "partially_paid": queryset.filter(
                    payment_status=Invoice.PaymentStatus.PARTIALLY_PAID
                ).count(),
                "cancelled": queryset.filter(
                    payment_status=Invoice.PaymentStatus.CANCELLED
                ).count(),
                "total_billed": queryset.aggregate(total=Sum("patient_payable"))["total"] or 0,
                "total_collected": queryset.aggregate(total=Sum("paid_amount"))["total"] or 0,
                "outstanding": sum((invoice.balance_due for invoice in pending), Decimal("0")),
                "by_service": list(
                    queryset.values("items__service_type")
                    .annotate(total=Sum("items__amount"))
                    .order_by("-total")
                ),
                "revenue_trend": revenue_trend,
            }
        )
