from rest_framework import serializers

from .models import Admission, DischargeSummary


class AdmissionSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    patient_code = serializers.CharField(source="patient.patient_id", read_only=True)
    patient_age = serializers.IntegerField(source="patient.age", read_only=True)
    doctor_name = serializers.CharField(source="doctor.name", read_only=True, default=None)
    attending_doctor_name = serializers.CharField(
        source="attending_doctor.name", read_only=True, default=None
    )
    department_name = serializers.CharField(
        source="department.name", read_only=True, default=None
    )
    ward_name = serializers.CharField(source="ward.name", read_only=True, default=None)
    nurse_name = serializers.CharField(source="nurse.name", read_only=True, default=None)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    length_of_stay = serializers.IntegerField(read_only=True)

    class Meta:
        model = Admission
        fields = [
            "id",
            "admission_id",
            "patient",
            "patient_name",
            "patient_code",
            "patient_age",
            "doctor",
            "doctor_name",
            "attending_doctor",
            "attending_doctor_name",
            "department",
            "department_name",
            "admission_date",
            "expected_discharge_date",
            "discharge_date",
            "ward",
            "ward_name",
            "bed",
            "bed_number",
            "nurse",
            "nurse_name",
            "admission_reason",
            "diagnosis",
            "treatment_plan",
            "status",
            "status_label",
            "length_of_stay",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["admission_id", "created_at", "updated_at"]


class AdmissionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admission
        fields = [
            "id",
            "admission_id",
            "patient",
            "doctor",
            "attending_doctor",
            "department",
            "admission_date",
            "expected_discharge_date",
            "discharge_date",
            "ward",
            "bed",
            "bed_number",
            "nurse",
            "admission_reason",
            "diagnosis",
            "treatment_plan",
            "status",
            "notes",
        ]
        read_only_fields = ["admission_id"]

    def validate(self, attrs):
        bed = attrs.get("bed")
        if bed is not None:
            occupant = bed.admissions.exclude(
                status__in=[
                    Admission.Status.DISCHARGED,
                    Admission.Status.TRANSFERRED,
                ]
            )
            if self.instance is not None:
                occupant = occupant.exclude(pk=self.instance.pk)
            if occupant.exists() or (
                bed.status == "occupied" and self.instance is None
            ):
                raise serializers.ValidationError(
                    {"bed": f"Bed {bed.bed_number} is not available for admission."}
                )
        if attrs.get("discharge_date") and attrs.get("expected_discharge_date"):
            if attrs["discharge_date"].date() > attrs["expected_discharge_date"]:
                pass  # discharging later than planned is allowed, no validation error
        return attrs

    def create(self, validated_data):
        if not validated_data.get("admission_id"):
            from config.ids import next_sequential_id

            validated_data["admission_id"] = next_sequential_id(
                Admission, "admission_id", "ADM", width=5
            )
        doctor = validated_data.get("doctor")
        if doctor and not validated_data.get("department"):
            validated_data["department"] = doctor.department
        if doctor and not validated_data.get("attending_doctor"):
            validated_data["attending_doctor"] = doctor
        bed = validated_data.get("bed")
        if bed is not None:
            validated_data["bed_number"] = bed.bed_number
            if not validated_data.get("ward"):
                validated_data["ward"] = bed.ward
        return super().create(validated_data)


class DischargeSummarySerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    patient_code = serializers.CharField(source="patient.patient_id", read_only=True)
    doctor_name = serializers.CharField(source="doctor.name", read_only=True, default=None)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    workflow_steps = serializers.ListField(read_only=True)
    workflow_progress = serializers.DictField(read_only=True)
    admission_code = serializers.CharField(
        source="admission.admission_id", read_only=True, default=None
    )

    class Meta:
        model = DischargeSummary
        fields = [
            "id",
            "discharge_id",
            "patient",
            "patient_name",
            "patient_code",
            "admission",
            "admission_code",
            "doctor",
            "doctor_name",
            "admission_date",
            "discharge_date",
            "diagnosis_summary",
            "procedures",
            "medications",
            "follow_up_instructions",
            "follow_up_date",
            "condition_on_discharge",
            "final_bill",
            "status",
            "status_label",
            "doctor_approved",
            "final_bill_settled",
            "pharmacy_cleared",
            "insurance_processed",
            "follow_up_scheduled",
            "workflow_steps",
            "workflow_progress",
            "approved_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["discharge_id", "approved_at", "created_at", "updated_at"]

    def create(self, validated_data):
        if not validated_data.get("discharge_id"):
            from config.ids import next_sequential_id

            validated_data["discharge_id"] = next_sequential_id(
                DischargeSummary, "discharge_id", "DS", width=5
            )
        return super().create(validated_data)
