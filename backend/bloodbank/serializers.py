from rest_framework import serializers

from .models import BloodIssue, BloodStock, Donation


class BloodStockSerializer(serializers.ModelSerializer):
    status = serializers.CharField(read_only=True)
    total_units = serializers.IntegerField(read_only=True)

    class Meta:
        model = BloodStock
        fields = [
            "id",
            "blood_group",
            "units_available",
            "units_reserved",
            "critical_threshold",
            "total_units",
            "status",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]


class DonationSerializer(serializers.ModelSerializer):
    screening_label = serializers.CharField(source="get_screening_display", read_only=True)

    class Meta:
        model = Donation
        fields = [
            "id",
            "donation_id",
            "donor_name",
            "donor_code",
            "blood_group",
            "units",
            "donation_date",
            "donor_age",
            "donor_gender",
            "donor_phone",
            "camp_location",
            "screening",
            "screening_label",
            "hemoglobin",
            "notes",
            "created_at",
        ]
        read_only_fields = ["donation_id", "created_at"]

    def create(self, validated_data):
        if not validated_data.get("donation_id"):
            from config.ids import next_sequential_id

            validated_data["donation_id"] = next_sequential_id(
                Donation, "donation_id", "DON", width=5
            )
        return super().create(validated_data)


class BloodIssueSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True, default=None)
    patient_code = serializers.CharField(
        source="patient.patient_id", read_only=True, default=None
    )
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = BloodIssue
        fields = [
            "id",
            "issue_id",
            "blood_group",
            "units",
            "patient",
            "patient_name",
            "patient_code",
            "ward",
            "reason",
            "crossmatch_id",
            "requested_at",
            "issued_at",
            "status",
            "status_label",
            "notes",
        ]
        read_only_fields = ["issue_id", "requested_at"]

    def create(self, validated_data):
        if not validated_data.get("issue_id"):
            from config.ids import next_sequential_id

            validated_data["issue_id"] = next_sequential_id(
                BloodIssue, "issue_id", "BIS", width=5
            )
        return super().create(validated_data)
