from rest_framework import serializers

from .models import EmergencyVisit


class EmergencyVisitSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    patient_code = serializers.CharField(source="patient.patient_id", read_only=True)
    patient_age = serializers.IntegerField(source="patient.age", read_only=True)
    patient_gender = serializers.CharField(
        source="patient.get_gender_display", read_only=True
    )
    blood_group = serializers.CharField(source="patient.blood_group", read_only=True)
    doctor_name = serializers.CharField(
        source="assigned_doctor.name", read_only=True, default=None
    )
    nurse_name = serializers.CharField(
        source="assigned_nurse.name", read_only=True, default=None
    )
    bed_number = serializers.CharField(
        source="bed.bed_number", read_only=True, default=None
    )
    priority_label = serializers.CharField(source="get_priority_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    waiting_minutes = serializers.IntegerField(read_only=True)

    class Meta:
        model = EmergencyVisit
        fields = [
            "id",
            "case_id",
            "patient",
            "patient_name",
            "patient_code",
            "patient_age",
            "patient_gender",
            "blood_group",
            "arrival_time",
            "triage_time",
            "priority",
            "priority_label",
            "assigned_doctor",
            "doctor_name",
            "assigned_nurse",
            "nurse_name",
            "bed",
            "bed_number",
            "chief_complaint",
            "condition_notes",
            "vitals_summary",
            "treatment_given",
            "disposition",
            "status",
            "status_label",
            "waiting_minutes",
            "closed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["case_id", "created_at", "updated_at", "waiting_minutes"]


class EmergencyVisitWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmergencyVisit
        fields = [
            "id",
            "case_id",
            "patient",
            "arrival_time",
            "triage_time",
            "priority",
            "assigned_doctor",
            "assigned_nurse",
            "bed",
            "chief_complaint",
            "condition_notes",
            "vitals_summary",
            "treatment_given",
            "disposition",
            "status",
            "closed_at",
        ]
        read_only_fields = ["case_id"]

    def validate_bed(self, value):
        if value is None:
            return value
        if value.status == "occupied" and value.emergency_cases.exclude(
            pk=getattr(self.instance, "pk", None)
        ).exists():
            raise serializers.ValidationError(
                f"Bed {value.bed_number} is already occupied."
            )
        return value

    def create(self, validated_data):
        if not validated_data.get("case_id"):
            from config.ids import next_sequential_id

            validated_data["case_id"] = next_sequential_id(
                EmergencyVisit, "case_id", "ER", width=5
            )
        return super().create(validated_data)
