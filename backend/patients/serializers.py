from rest_framework import serializers

from .models import NurseAssignment, Patient, Vitals


class PatientListSerializer(serializers.ModelSerializer):
    age = serializers.IntegerField(read_only=True)
    gender_label = serializers.CharField(source="get_gender_display", read_only=True)
    department_name = serializers.CharField(
        source="department.name", read_only=True, default=None
    )
    doctor_name = serializers.CharField(
        source="assigned_doctor.name", read_only=True, default=None
    )
    doctor_id = serializers.CharField(
        source="assigned_doctor.doctor_id", read_only=True, default=None
    )
    patient_type_label = serializers.CharField(
        source="get_patient_type_display", read_only=True
    )
    status_label = serializers.CharField(
        source="get_current_status_display", read_only=True
    )

    class Meta:
        model = Patient
        fields = [
            "id",
            "patient_id",
            "name",
            "age",
            "gender",
            "gender_label",
            "blood_group",
            "phone",
            "department",
            "department_name",
            "assigned_doctor",
            "doctor_name",
            "doctor_id",
            "registration_date",
            "patient_type",
            "patient_type_label",
            "current_status",
            "status_label",
            "admission_status",
            "insurance_provider",
        ]


class PatientSerializer(serializers.ModelSerializer):
    age = serializers.IntegerField(read_only=True)
    gender_label = serializers.CharField(source="get_gender_display", read_only=True)
    department_name = serializers.CharField(
        source="department.name", read_only=True, default=None
    )
    doctor_name = serializers.CharField(
        source="assigned_doctor.name", read_only=True, default=None
    )
    patient_type_label = serializers.CharField(
        source="get_patient_type_display", read_only=True
    )
    status_label = serializers.CharField(
        source="get_current_status_display", read_only=True
    )
    admission_status_label = serializers.CharField(
        source="get_admission_status_display", read_only=True
    )
    allergy_list = serializers.ListField(child=serializers.CharField(), read_only=True)
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = [
            "id",
            "patient_id",
            "name",
            "age",
            "date_of_birth",
            "gender",
            "gender_label",
            "blood_group",
            "photo",
            "photo_url",
            "phone",
            "email",
            "address",
            "city",
            "state",
            "postal_code",
            "emergency_contact_name",
            "emergency_contact_phone",
            "emergency_contact_relation",
            "department",
            "department_name",
            "assigned_doctor",
            "doctor_name",
            "registration_date",
            "patient_type",
            "patient_type_label",
            "current_status",
            "status_label",
            "admission_status",
            "admission_status_label",
            "allergies",
            "allergy_list",
            "medical_history",
            "chronic_conditions",
            "height_cm",
            "weight_kg",
            "insurance_provider",
            "insurance_policy_number",
            "notes",
            "is_demo",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "is_demo", "patient_id"]

    def get_photo_url(self, obj):
        if not obj.photo:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.photo.url) if request else obj.photo.url


class PatientWriteSerializer(serializers.ModelSerializer):
    """Validation heavy serializer used for registration and updates."""

    class Meta:
        model = Patient
        fields = [
            "id",
            "patient_id",
            "name",
            "date_of_birth",
            "gender",
            "blood_group",
            "phone",
            "email",
            "address",
            "city",
            "state",
            "postal_code",
            "emergency_contact_name",
            "emergency_contact_phone",
            "emergency_contact_relation",
            "department",
            "assigned_doctor",
            "registration_date",
            "patient_type",
            "current_status",
            "admission_status",
            "allergies",
            "medical_history",
            "chronic_conditions",
            "height_cm",
            "weight_kg",
            "insurance_provider",
            "insurance_policy_number",
            "notes",
        ]
        extra_kwargs = {"patient_id": {"required": False}}

    def validate_phone(self, value):
        digits = "".join(ch for ch in value if ch.isdigit())
        if value and len(digits) < 10:
            raise serializers.ValidationError(
                "Enter a contact number with at least 10 digits (this is demo data)."
            )
        return value

    def validate(self, attrs):
        doctor = attrs.get("assigned_doctor") or getattr(
            self.instance, "assigned_doctor", None
        )
        department = attrs.get("department") or getattr(self.instance, "department", None)
        if doctor and department and doctor.department_id != department.id:
            raise serializers.ValidationError(
                {
                    "assigned_doctor": (
                        f"{doctor.name} belongs to {doctor.department.name}; "
                        f"select a {department.name} doctor or change the department."
                    )
                }
            )
        return attrs

    def create(self, validated_data):
        if not validated_data.get("patient_id"):
            from .services import next_patient_id

            validated_data["patient_id"] = next_patient_id()
        return super().create(validated_data)


class VitalsSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    patient_code = serializers.CharField(source="patient.patient_id", read_only=True)
    recorded_by_name = serializers.CharField(
        source="recorded_by.full_name", read_only=True, default=None
    )
    blood_pressure = serializers.CharField(read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Vitals
        fields = [
            "id",
            "patient",
            "patient_name",
            "patient_code",
            "recorded_by",
            "recorded_by_name",
            "recorded_at",
            "temperature_c",
            "pulse_bpm",
            "respiratory_rate",
            "bp_systolic",
            "bp_diastolic",
            "blood_pressure",
            "spo2",
            "blood_glucose",
            "pain_score",
            "weight_kg",
            "height_cm",
            "status",
            "status_label",
            "notes",
            "created_at",
        ]
        read_only_fields = ["created_at", "recorded_by", "status"]

    def validate(self, attrs):
        systolic = attrs.get("bp_systolic")
        diastolic = attrs.get("bp_diastolic")
        if systolic and diastolic and diastolic >= systolic:
            raise serializers.ValidationError(
                {"bp_diastolic": "Diastolic pressure must be lower than systolic pressure."}
            )
        return attrs

    def create(self, validated_data):
        validated_data["status"] = _vitals_status(validated_data)
        request = self.context.get("request")
        if request is not None and request.user.is_authenticated:
            validated_data["recorded_by"] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        merged = {field: getattr(instance, field) for field in _VITAL_FIELDS}
        merged.update(validated_data)
        validated_data["status"] = _vitals_status(merged)
        return super().update(instance, validated_data)


_VITAL_FIELDS = (
    "temperature_c",
    "pulse_bpm",
    "respiratory_rate",
    "bp_systolic",
    "bp_diastolic",
    "spo2",
)


def _vitals_status(values):
    """Flag obviously out-of-range demo observations for the UI badge."""
    abnormal = False
    critical = False

    temperature = values.get("temperature_c")
    if temperature is not None:
        temperature = float(temperature)
        abnormal = abnormal or temperature >= 37.8 or temperature <= 35.5
        critical = critical or temperature >= 39.5 or temperature <= 34.5

    pulse = values.get("pulse_bpm")
    if pulse:
        abnormal = abnormal or pulse >= 100 or pulse <= 55
        critical = critical or pulse >= 140 or pulse <= 40

    spo2 = values.get("spo2")
    if spo2:
        abnormal = abnormal or spo2 < 95
        critical = critical or spo2 < 90

    systolic = values.get("bp_systolic")
    if systolic:
        abnormal = abnormal or systolic >= 140 or systolic <= 90
        critical = critical or systolic >= 180 or systolic <= 80

    if critical:
        return Vitals.Status.CRITICAL
    if abnormal:
        return Vitals.Status.ABNORMAL
    return Vitals.Status.NORMAL


class NurseAssignmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    patient_code = serializers.CharField(source="patient.patient_id", read_only=True)
    nurse_name = serializers.CharField(source="nurse.name", read_only=True)
    nurse_employee_id = serializers.CharField(source="nurse.employee_id", read_only=True)
    shift_name = serializers.CharField(source="shift.name", read_only=True, default=None)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = NurseAssignment
        fields = [
            "id",
            "patient",
            "patient_name",
            "patient_code",
            "nurse",
            "nurse_name",
            "nurse_employee_id",
            "shift",
            "shift_name",
            "assigned_on",
            "status",
            "status_label",
            "notes",
            "created_at",
        ]
        read_only_fields = ["created_at"]
