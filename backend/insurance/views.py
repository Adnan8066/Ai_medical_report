from datetime import date

from django.db.models import Count, Sum
from rest_framework.decorators import action
from rest_framework.response import Response

from config.viewsets import BaseReadOnlyViewSet, BaseViewSet

from .models import InsuranceClaim, InsurancePolicy, InsuranceProvider
from .serializers import (
    InsuranceClaimSerializer,
    InsurancePolicySerializer,
    InsuranceProviderSerializer,
)


class InsuranceProviderViewSet(BaseReadOnlyViewSet):
    module = "insurance"
    queryset = InsuranceProvider.objects.prefetch_related("policies").all()
    serializer_class = InsuranceProviderSerializer
    search_fields = ["name", "code", "contact_person"]
    ordering = ["name"]
    pagination_class = None


class InsurancePolicyViewSet(BaseViewSet):
    module = "insurance"
    queryset = InsurancePolicy.objects.select_related("patient", "provider").all()
    serializer_class = InsurancePolicySerializer
    search_fields = ["policy_number", "patient__name", "patient__patient_id", "provider__name"]
    ordering = ["-valid_to"]
    apply_patient_scope = True
    patient_lookup = "patient"


class InsuranceClaimViewSet(BaseViewSet):
    module = "insurance"
    queryset = InsuranceClaim.objects.select_related(
        "policy", "policy__provider", "patient", "invoice"
    ).all()
    serializer_class = InsuranceClaimSerializer
    search_fields = ["claim_number", "patient__name", "patient__patient_id", "policy__policy_number"]
    ordering = ["-submitted_date"]
    apply_patient_scope = True
    patient_lookup = "patient"

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        if status_value := params.get("status"):
            queryset = queryset.filter(status=status_value)
        if patient := params.get("patient"):
            queryset = queryset.filter(patient_id=patient)
        if provider := params.get("provider"):
            queryset = queryset.filter(policy__provider_id=provider)
        return queryset

    @action(detail=True, methods=["post"])
    def set_status(self, request, pk=None):
        """Progress a claim through review, approval, rejection or settlement."""
        claim = self.get_object()
        new_status = request.data.get("status")
        if new_status not in dict(InsuranceClaim.Status.choices):
            return Response(
                {
                    "detail": "Unknown claim status.",
                    "code": "invalid",
                    "errors": {
                        "status": f"Choose one of: {', '.join(dict(InsuranceClaim.Status.choices))}."
                    },
                },
                status=400,
            )
        claim.status = new_status
        if new_status in {
            InsuranceClaim.Status.APPROVED,
            InsuranceClaim.Status.PARTIALLY_APPROVED,
            InsuranceClaim.Status.REJECTED,
        }:
            claim.reviewed_date = date.today()
            if request.data.get("approved_amount") is not None:
                claim.approved_amount = request.data["approved_amount"]
            if new_status == InsuranceClaim.Status.REJECTED:
                claim.rejection_reason = request.data.get("rejection_reason", "")
        if new_status == InsuranceClaim.Status.SETTLED:
            claim.settled_date = date.today()
        claim.handled_by = request.user
        claim.save()
        self._audit("Updated claim status for", claim)
        return Response(InsuranceClaimSerializer(claim).data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        queryset = self.get_queryset()
        return Response(
            {
                "total": queryset.count(),
                "submitted": queryset.filter(
                    status=InsuranceClaim.Status.SUBMITTED
                ).count(),
                "under_review": queryset.filter(
                    status=InsuranceClaim.Status.UNDER_REVIEW
                ).count(),
                "approved": queryset.filter(
                    status__in=[
                        InsuranceClaim.Status.APPROVED,
                        InsuranceClaim.Status.PARTIALLY_APPROVED,
                    ]
                ).count(),
                "rejected": queryset.filter(status=InsuranceClaim.Status.REJECTED).count(),
                "settled": queryset.filter(status=InsuranceClaim.Status.SETTLED).count(),
                "pending": queryset.filter(
                    status__in=[
                        InsuranceClaim.Status.SUBMITTED,
                        InsuranceClaim.Status.UNDER_REVIEW,
                    ]
                ).count(),
                "claimed_amount": queryset.aggregate(total=Sum("claim_amount"))["total"] or 0,
                "approved_amount": queryset.aggregate(total=Sum("approved_amount"))["total"]
                or 0,
                "rejected_amount": queryset.aggregate(total=Sum("rejected_amount"))["total"]
                or 0,
                "by_provider": list(
                    queryset.values("policy__provider__name")
                    .annotate(total=Count("id"), amount=Sum("claim_amount"))
                    .order_by("-total")
                ),
            }
        )
