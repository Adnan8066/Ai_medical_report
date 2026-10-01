from rest_framework import serializers

from .models import Bed, Ward


class WardSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(
        source="department.name", read_only=True, default=None
    )
    category_label = serializers.CharField(source="get_category_display", read_only=True)
    total_beds = serializers.IntegerField(source="beds.count", read_only=True)
    available_beds = serializers.SerializerMethodField()
    occupied_beds = serializers.SerializerMethodField()

    class Meta:
        model = Ward
        fields = [
            "id",
            "name",
            "code",
            "department",
            "department_name",
            "floor",
            "category",
            "category_label",
            "description",
            "is_active",
            "total_beds",
            "available_beds",
            "occupied_beds",
        ]

    def get_available_beds(self, obj):
        return obj.beds.filter(status=Bed.Status.AVAILABLE).count()

    def get_occupied_beds(self, obj):
        return obj.beds.filter(status=Bed.Status.OCCUPIED).count()


class BedSerializer(serializers.ModelSerializer):
    ward_name = serializers.CharField(source="ward.name", read_only=True, default=None)
    department_name = serializers.CharField(
        source="department.name", read_only=True, default=None
    )
    category_label = serializers.CharField(source="get_category_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    patient_name = serializers.CharField(source="patient.name", read_only=True, default=None)
    patient_code = serializers.CharField(
        source="patient.patient_id", read_only=True, default=None
    )

    class Meta:
        model = Bed
        fields = [
            "id",
            "bed_number",
            "ward",
            "ward_name",
            "department",
            "department_name",
            "category",
            "category_label",
            "status",
            "status_label",
            "floor",
            "room_number",
            "patient",
            "patient_name",
            "patient_code",
            "daily_rate",
            "has_oxygen",
            "has_ventilator",
            "is_monitored",
            "notes",
            "last_cleaned_at",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]


class BedAssignSerializer(serializers.Serializer):
    patient = serializers.IntegerField()
    ward = serializers.IntegerField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True)
