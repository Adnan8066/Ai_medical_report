from rest_framework import serializers

from .models import Doctor


class DoctorSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)
    department_code = serializers.CharField(source="department.code", read_only=True)
    designation_label = serializers.CharField(
        source="get_designation_display", read_only=True
    )
    availability_label = serializers.CharField(
        source="get_availability_display", read_only=True
    )
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    photo_url = serializers.SerializerMethodField()
    patient_count = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = [
            "id",
            "doctor_id",
            "name",
            "short_name",
            "gender",
            "photo",
            "photo_url",
            "department",
            "department_name",
            "department_code",
            "designation",
            "designation_label",
            "is_hod",
            "qualification",
            "experience_years",
            "specialization",
            "consultation_fee",
            "room_number",
            "phone_extension",
            "phone",
            "email",
            "availability",
            "availability_label",
            "available_days",
            "opd_schedule",
            "joining_date",
            "languages",
            "about",
            "status",
            "status_label",
            "patient_count",
            "is_demo",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "short_name", "is_demo"]

    def get_photo_url(self, obj):
        if not obj.photo:
            return None
        request = self.context.get("request")
        url = obj.photo.url
        return request.build_absolute_uri(url) if request else url

    def get_patient_count(self, obj):
        return obj.patients.count() if hasattr(obj, "patients") else 0


class DoctorListSerializer(serializers.ModelSerializer):
    """Trimmed payload for tables and pickers."""

    department_name = serializers.CharField(source="department.name", read_only=True)
    designation_label = serializers.CharField(source="get_designation_display", read_only=True)
    availability_label = serializers.CharField(
        source="get_availability_display", read_only=True
    )

    class Meta:
        model = Doctor
        fields = [
            "id",
            "doctor_id",
            "name",
            "department",
            "department_name",
            "designation_label",
            "is_hod",
            "specialization",
            "consultation_fee",
            "room_number",
            "availability",
            "availability_label",
            "available_days",
            "status",
            "experience_years",
        ]
