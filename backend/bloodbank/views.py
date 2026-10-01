from datetime import date, timedelta

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework import status as http_status
from rest_framework.decorators import action
from rest_framework.response import Response

from config.viewsets import BaseViewSet

from .models import BLOOD_GROUPS, BloodIssue, BloodStock, Donation
from .serializers import BloodIssueSerializer, BloodStockSerializer, DonationSerializer


class BloodStockViewSet(BaseViewSet):
    module = "bloodbank"
    queryset = BloodStock.objects.all()
    serializer_class = BloodStockSerializer
    pagination_class = None
    ordering = ["blood_group"]

    @action(detail=False, methods=["get"])
    def dashboard(self, request):
        """Blood bank overview: stock levels, expiry exposure and activity."""
        stocks = BloodStock.objects.all()
        horizon = date.today() + timedelta(days=30)
        recent_donations = Donation.objects.filter(
            donation_date__gte=date.today() - timedelta(days=30)
        )
        recent_issues = BloodIssue.objects.filter(
            requested_at__date__gte=date.today() - timedelta(days=30)
        )
        return Response(
            {
                "stock": BloodStockSerializer(stocks, many=True).data,
                "summary": {
                    "total_available": stocks.aggregate(total=Sum("units_available"))[
                        "total"
                    ]
                    or 0,
                    "total_reserved": stocks.aggregate(total=Sum("units_reserved"))["total"]
                    or 0,
                    "critical_groups": [
                        item.blood_group
                        for item in stocks
                        if item.status in {"critical", "out_of_stock"}
                    ],
                    "groups_in_stock": sum(1 for item in stocks if item.units_available > 0),
                },
                "donations": {
                    "last_30_days": recent_donations.count(),
                    "units_collected": recent_donations.aggregate(total=Sum("units"))[
                        "total"
                    ]
                    or 0,
                    "by_group": list(
                        recent_donations.values("blood_group")
                        .annotate(total=Sum("units"))
                        .order_by("blood_group")
                    ),
                },
                "issues": {
                    "last_30_days": recent_issues.count(),
                    "units_issued": recent_issues.aggregate(total=Sum("units"))["total"] or 0,
                },
                "expiring_soon": [],
                "notice": (
                    "All blood bank records in this demo are fictional and for "
                    "demonstration only."
                ),
                "expiry_horizon": horizon,
            }
        )

    @action(detail=False, methods=["get"])
    def compatible(self, request):
        """Simple compatibility reference used by the issue form."""
        mapping = {
            "O-": ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"],
            "O+": ["O+", "A+", "B+", "AB+"],
            "A-": ["A-", "A+", "AB-", "AB+"],
            "A+": ["A+", "AB+"],
            "B-": ["B-", "B+", "AB-", "AB+"],
            "B+": ["B+", "AB+"],
            "AB-": ["AB-", "AB+"],
            "AB+": ["AB+"],
        }
        return Response(mapping)


class DonationViewSet(BaseViewSet):
    module = "bloodbank"
    queryset = Donation.objects.all()
    serializer_class = DonationSerializer
    search_fields = ["donation_id", "donor_name", "donor_code", "blood_group"]
    ordering = ["-donation_date"]

    def perform_create(self, serializer):
        with transaction.atomic():
            donation = serializer.save(recorded_by=self.request.user)
            if donation.screening == Donation.Screening.PASSED:
                stock, _ = BloodStock.objects.select_for_update().get_or_create(
                    blood_group=donation.blood_group
                )
                stock.units_available += donation.units
                stock.save(update_fields=["units_available", "updated_at"])
            self._audit("Recorded donation", donation)
        return donation

    @action(detail=False, methods=["get"])
    def stats(self, request):
        queryset = self.get_queryset()
        return Response(
            {
                "total": queryset.count(),
                "units_collected": queryset.aggregate(total=Sum("units"))["total"] or 0,
                "passed": queryset.filter(screening=Donation.Screening.PASSED).count(),
                "pending": queryset.filter(screening=Donation.Screening.PENDING).count(),
                "failed": queryset.filter(screening=Donation.Screening.FAILED).count(),
                "by_group": list(
                    queryset.values("blood_group")
                    .annotate(total=Sum("units"))
                    .order_by("blood_group")
                ),
            }
        )


class BloodIssueViewSet(BaseViewSet):
    module = "bloodbank"
    queryset = BloodIssue.objects.select_related("patient").all()
    serializer_class = BloodIssueSerializer
    search_fields = ["issue_id", "patient__name", "crossmatch_id"]
    ordering = ["-requested_at"]

    def perform_create(self, serializer):
        with transaction.atomic():
            issue = serializer.save()
            stock, _ = BloodStock.objects.select_for_update().get_or_create(
                blood_group=issue.blood_group
            )
            if issue.status == BloodIssue.Status.RESERVED:
                stock.units_reserved += issue.units
                stock.save(update_fields=["units_reserved", "updated_at"])
            self._audit("Raised blood request", issue)
        return issue

    @action(detail=True, methods=["post"])
    def issue_units(self, request, pk=None):
        """Release reserved units to the ward."""
        issue = self.get_object()
        with transaction.atomic():
            stock, _ = BloodStock.objects.select_for_update().get_or_create(
                blood_group=issue.blood_group
            )
            if stock.units_available < issue.units:
                return Response(
                    {
                        "detail": f"Only {stock.units_available} units of {issue.blood_group} available.",
                        "code": "invalid",
                        "errors": {"units": "Reduce the requested units."},
                    },
                    status=http_status.HTTP_400_BAD_REQUEST,
                )
            if issue.status == BloodIssue.Status.RESERVED:
                stock.units_reserved = max(0, stock.units_reserved - issue.units)
            stock.units_available -= issue.units
            stock.save(update_fields=["units_available", "units_reserved", "updated_at"])
            issue.status = BloodIssue.Status.ISSUED
            issue.issued_at = timezone.now()
            issue.issued_by = request.user
            issue.save(update_fields=["status", "issued_at", "issued_by"])
            self._audit("Issued blood units", issue)
        return Response(BloodIssueSerializer(issue).data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        queryset = self.get_queryset()
        return Response(
            {
                "total": queryset.count(),
                "reserved": queryset.filter(status=BloodIssue.Status.RESERVED).count(),
                "issued": queryset.filter(status=BloodIssue.Status.ISSUED).count(),
                "units_issued": queryset.filter(status=BloodIssue.Status.ISSUED).aggregate(
                    total=Sum("units")
                )["total"]
                or 0,
                "by_group": list(
                    queryset.values("blood_group")
                    .annotate(total=Sum("units"))
                    .order_by("blood_group")
                ),
            }
        )
