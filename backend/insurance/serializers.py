from rest_framework import serializers

from .models import InsuranceClaim, InsurancePolicy, InsuranceProvider


class InsuranceProviderSerializer(serializers.ModelSerializer):
    policy_count = serializers.IntegerField(source="policies.count", read_only=True)

    class Meta:
        model = InsuranceProvider
        fields = [
            "id",
            "name",
            "code",
            "contact_person",
            "phone",
            "email",
            "address",
            "claim_portal",
            "policy_count",
        ]


class InsurancePolicySerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    patient_code = serializers.CharField(source="patient.patient_id", read_only=True)
    provider_name = serializers.CharField(source="provider.name", read_only=True)
    policy_type_label = serializers.CharField(
        source="get_policy_type_display", read_only=True
    )
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    claims_count = serializers.IntegerField(source="claims.count", read_only=True)

    class Meta:
        model = InsurancePolicy
        fields = [
            "id",
            "policy_number",
            "patient",
            "patient_name",
            "patient_code",
            "provider",
            "provider_name",
            "policy_type",
            "policy_type_label",
            "coverage_amount",
            "valid_from",
            "valid_to",
            "corporate_account",
            "status",
            "status_label",
            "claims_count",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class InsuranceClaimSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    patient_code = serializers.CharField(source="patient.patient_id", read_only=True)
    policy_number = serializers.CharField(source="policy.policy_number", read_only=True)
    provider_name = serializers.CharField(
        source="policy.provider.name", read_only=True, default=None
    )
    invoice_number = serializers.CharField(
        source="invoice.invoice_number", read_only=True, default=None
    )
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    balance_amount = serializers.SerializerMethodField()

    class Meta:
        model = InsuranceClaim
        fields = [
            "id",
            "claim_number",
            "policy",
            "policy_number",
            "provider_name",
            "patient",
            "patient_name",
            "patient_code",
            "invoice",
            "invoice_number",
            "claim_amount",
            "approved_amount",
            "rejected_amount",
            "balance_amount",
            "status",
            "status_label",
            "submitted_date",
            "reviewed_date",
            "settled_date",
            "diagnosis_code",
            "treatment_summary",
            "rejection_reason",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["claim_number", "created_at", "updated_at"]

    def get_balance_amount(self, obj):
        return (obj.claim_amount or 0) - (obj.approved_amount or 0)

    def validate(self, attrs):
        claim_amount = attrs.get("claim_amount")
        if claim_amount is not None and claim_amount <= 0:
            raise serializers.ValidationError(
                {"claim_amount": "The claim amount must be greater than zero."}
            )
        policy = attrs.get("policy") or getattr(self.instance, "policy", None)
        patient = attrs.get("patient") or getattr(self.instance, "patient", None)
        if policy and patient and policy.patient_id != patient.id:
            raise serializers.ValidationError(
                {"policy": "This policy belongs to a different patient."}
            )
        return attrs

    def create(self, validated_data):
        if not validated_data.get("claim_number"):
            from config.ids import next_sequential_id

            validated_data["claim_number"] = next_sequential_id(
                InsuranceClaim, "claim_number", "CLM", width=5
            )
        return super().create(validated_data)
