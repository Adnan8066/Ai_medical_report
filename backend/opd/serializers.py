from rest_framework import serializers

from .models import OPDVisit


class OPDVisitSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    patient_code = serializers.CharField(source="patient.patient_id", read_only=True)
    patient_age = serializers.IntegerField(source="patient.age", read_only=True)
    patient_gender = serializers.CharField(
        source="patient.get_gender_display", read_only=True
    )
    doctor_name = serializers.CharField(source="doctor.name", read_only=True)
    department_name = serializers.CharField(
        source="department.name", read_only=True, default=None
    )
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = OPDVisit
        fields = [
            "id",
            "visit_id",
            "patient",
            "patient_name",
            "patient_code",
            "patient_age",
            "patient_gender",
            "doctor",
            "doctor_name",
            "department",
            "department_name",
            "appointment",
            "visit_date",
            "visit_time",
            "chief_complaint",
            "symptoms",
            "consultation_notes",
            "diagnosis",
            "prescription_notes",
            "advice",
            "follow_up_date",
            "consultation_fee",
            "status",
            "status_label",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["visit_id", "created_at", "updated_at"]


class OPDVisitWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = OPDVisit
        fields = [
            "id",
            "visit_id",
            "patient",
            "doctor",
            "department",
            "appointment",
            "visit_date",
            "visit_time",
            "chief_complaint",
            "symptoms",
            "consultation_notes",
            "diagnosis",
            "prescription_notes",
            "advice",
            "follow_up_date",
            "consultation_fee",
            "status",
        ]
        read_only_fields = ["visit_id"]

    def validate(self, attrs):
        visit_date = attrs.get("visit_date") or getattr(self.instance, "visit_date", None)
        follow_up = attrs.get("follow_up_date")
        if follow_up and visit_date and follow_up < visit_date:
            raise serializers.ValidationError(
                {"follow_up_date": "The follow-up date cannot be before the visit date."}
            )
        doctor = attrs.get("doctor") or getattr(self.instance, "doctor", None)
        department = attrs.get("department") or getattr(self.instance, "department", None)
        if doctor and department and doctor.department_id != department.id:
            raise serializers.ValidationError(
                {"department": f"{doctor.name} belongs to {doctor.department.name}."}
            )
        return attrs

    def create(self, validated_data):
        if not validated_data.get("visit_id"):
            from config.ids import next_sequential_id

            validated_data["visit_id"] = next_sequential_id(
                OPDVisit, "visit_id", "OPD", width=5
            )
        if validated_data.get("department") is None and validated_data.get("doctor"):
            validated_data["department"] = validated_data["doctor"].department
        if not validated_data.get("consultation_fee") and validated_data.get("doctor"):
            validated_data["consultation_fee"] = validated_data["doctor"].consultation_fee
        return super().create(validated_data)
