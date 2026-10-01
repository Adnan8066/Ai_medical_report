from rest_framework import serializers

from .models import RadiologyReport


class RadiologyReportSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    patient_code = serializers.CharField(source="patient.patient_id", read_only=True)
    doctor_name = serializers.CharField(source="doctor.name", read_only=True, default=None)
    scan_type_label = serializers.CharField(source="get_scan_type_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = RadiologyReport
        fields = [
            "id",
            "scan_id",
            "patient",
            "patient_name",
            "patient_code",
            "doctor",
            "doctor_name",
            "scan_type",
            "scan_type_label",
            "body_part",
            "appointment_date",
            "radiologist",
            "radiologist_name",
            "technician_name",
            "status",
            "status_label",
            "findings",
            "impression",
            "report",
            "report_date",
            "price",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["scan_id", "created_at", "updated_at"]


class RadiologyReportWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = RadiologyReport
        fields = [
            "id",
            "scan_id",
            "patient",
            "doctor",
            "scan_type",
            "body_part",
            "appointment_date",
            "radiologist_name",
            "technician_name",
            "status",
            "findings",
            "impression",
            "report",
            "report_date",
            "price",
        ]
        read_only_fields = ["scan_id"]

    def validate(self, attrs):
        status_value = attrs.get("status") or getattr(self.instance, "status", None)
        if status_value == RadiologyReport.Status.COMPLETED:
            findings = attrs.get("findings") or getattr(self.instance, "findings", "")
            if not findings:
                raise serializers.ValidationError(
                    {"findings": "Findings are required before completing the report."}
                )
        return attrs

    def create(self, validated_data):
        if not validated_data.get("scan_id"):
            from config.ids import next_sequential_id

            validated_data["scan_id"] = next_sequential_id(
                RadiologyReport, "scan_id", "RAD", width=5
            )
        return super().create(validated_data)
