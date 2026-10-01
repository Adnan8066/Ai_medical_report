from rest_framework import serializers

from .models import LabReport, LabTest
from .services import evaluate_flag


class LabTestSerializer(serializers.ModelSerializer):
    category_label = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = LabTest
        fields = [
            "id",
            "code",
            "name",
            "category",
            "category_label",
            "sample_type",
            "unit",
            "reference_range",
            "turnaround_hours",
            "price",
            "description",
            "is_active",
        ]


class LabReportSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    patient_code = serializers.CharField(source="patient.patient_id", read_only=True)
    doctor_name = serializers.CharField(source="doctor.name", read_only=True, default=None)
    test_name = serializers.CharField(source="test.name", read_only=True, default=None)
    test_code = serializers.CharField(source="test.code", read_only=True, default=None)
    test_category = serializers.CharField(
        source="test.get_category_display", read_only=True, default=None
    )
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    flag_label = serializers.CharField(source="get_flag_display", read_only=True)

    class Meta:
        model = LabReport
        fields = [
            "id",
            "lab_id",
            "patient",
            "patient_name",
            "patient_code",
            "doctor",
            "doctor_name",
            "test",
            "test_name",
            "test_code",
            "test_category",
            "ordered_at",
            "sample_collected_at",
            "report_date",
            "result",
            "numeric_value",
            "unit",
            "reference_range",
            "flag",
            "flag_label",
            "status",
            "status_label",
            "technician",
            "technician_name",
            "remarks",
            "price",
            "updated_at",
        ]
        read_only_fields = ["lab_id", "ordered_at", "updated_at", "flag"]


class LabReportWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabReport
        fields = [
            "id",
            "lab_id",
            "patient",
            "doctor",
            "test",
            "sample_collected_at",
            "report_date",
            "result",
            "numeric_value",
            "unit",
            "reference_range",
            "status",
            "technician_name",
            "remarks",
            "price",
        ]
        read_only_fields = ["lab_id"]

    def validate(self, attrs):
        status_value = attrs.get("status") or getattr(self.instance, "status", None)
        if status_value == LabReport.Status.COMPLETED:
            result = attrs.get("result") or getattr(self.instance, "result", "")
            if not result:
                raise serializers.ValidationError(
                    {"result": "A result value is required before completing the report."}
                )
        return attrs

    def _with_flag(self, validated_data):
        numeric = validated_data.get("numeric_value")
        if numeric is None and self.instance is not None:
            numeric = self.instance.numeric_value
        reference = validated_data.get("reference_range")
        test = validated_data.get("test") or getattr(self.instance, "test", None)
        if not reference and test is not None:
            reference = test.reference_range
            validated_data.setdefault("reference_range", reference)
        if not validated_data.get("unit") and test is not None:
            validated_data.setdefault("unit", test.unit)
        validated_data["flag"] = evaluate_flag(numeric, reference)
        return validated_data

    def create(self, validated_data):
        if not validated_data.get("lab_id"):
            from config.ids import next_sequential_id

            validated_data["lab_id"] = next_sequential_id(
                LabReport, "lab_id", "LAB", width=5
            )
        test = validated_data.get("test")
        if test is not None:
            validated_data.setdefault("price", test.price)
            validated_data.setdefault("reference_range", test.reference_range)
            validated_data.setdefault("unit", test.unit)
        self._with_flag(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        self._with_flag(validated_data)
        return super().update(instance, validated_data)
