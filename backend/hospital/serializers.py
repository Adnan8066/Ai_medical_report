from rest_framework import serializers

from .models import Department, Floor, Hospital, MapLocation


class HospitalSerializer(serializers.ModelSerializer):
    full_address = serializers.CharField(read_only=True)
    available_beds = serializers.SerializerMethodField()
    occupied_beds = serializers.SerializerMethodField()
    departments = serializers.SerializerMethodField()
    doctors = serializers.SerializerMethodField()
    nurses = serializers.SerializerMethodField()
    staff = serializers.SerializerMethodField()

    class Meta:
        model = Hospital
        fields = [
            "id",
            "name",
            "code",
            "hospital_type",
            "established_year",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "postal_code",
            "country",
            "full_address",
            "phone",
            "emergency_number",
            "email",
            "website",
            "registration_number",
            "total_beds",
            "icu_beds",
            "emergency_beds",
            "available_beds",
            "occupied_beds",
            "departments",
            "doctors",
            "nurses",
            "staff",
            "about",
            "logo",
            "is_demo",
            "updated_at",
        ]

    def _bed_counts(self):
        if not hasattr(self, "_bed_counts_cache"):
            from beds.models import Bed

            self._bed_counts_cache = {
                "available": Bed.objects.filter(status=Bed.Status.AVAILABLE).count(),
                "occupied": Bed.objects.filter(
                    status__in=[Bed.Status.OCCUPIED, Bed.Status.RESERVED]
                ).count(),
            }
        return self._bed_counts_cache

    def get_available_beds(self, obj):
        return self._bed_counts()["available"]

    def get_occupied_beds(self, obj):
        return self._bed_counts()["occupied"]

    def get_departments(self, obj):
        return Department.objects.filter(is_active=True).count()

    def get_doctors(self, obj):
        from doctors.models import Doctor

        return Doctor.objects.filter(status="active").count()

    def get_nurses(self, obj):
        from staff.models import Staff

        return Staff.objects.filter(role__icontains="nurse").count()

    def get_staff(self, obj):
        from staff.models import Staff

        return Staff.objects.count()


class DepartmentSerializer(serializers.ModelSerializer):
    hod_name = serializers.CharField(source="hod.name", read_only=True, default=None)
    hod_qualification = serializers.CharField(
        source="hod.qualification", read_only=True, default=None
    )
    doctor_count = serializers.SerializerMethodField()
    bed_count_actual = serializers.SerializerMethodField()
    occupied_beds = serializers.SerializerMethodField()
    patient_count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = [
            "id",
            "name",
            "code",
            "hod",
            "hod_name",
            "hod_qualification",
            "floor",
            "location",
            "contact_extension",
            "phone",
            "email",
            "bed_count",
            "bed_count_actual",
            "occupied_beds",
            "doctor_count",
            "patient_count",
            "description",
            "is_clinical",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def get_doctor_count(self, obj):
        return obj.doctors.count() if hasattr(obj, "doctors") else 0

    def get_bed_count_actual(self, obj):
        return obj.beds.count() if hasattr(obj, "beds") else 0

    def get_occupied_beds(self, obj):
        if not hasattr(obj, "beds"):
            return 0
        return obj.beds.filter(status="occupied").count()

    def get_patient_count(self, obj):
        return obj.patients.count() if hasattr(obj, "patients") else 0


class FloorSerializer(serializers.ModelSerializer):
    location_count = serializers.IntegerField(source="locations.count", read_only=True)

    class Meta:
        model = Floor
        fields = ["id", "number", "name", "description", "is_public", "location_count"]


class MapLocationSerializer(serializers.ModelSerializer):
    floor_number = serializers.IntegerField(source="floor.number", read_only=True)
    floor_name = serializers.CharField(source="floor.name", read_only=True)
    department_code = serializers.CharField(
        source="department.code", read_only=True, default=None
    )

    class Meta:
        model = MapLocation
        fields = [
            "id",
            "floor",
            "floor_number",
            "floor_name",
            "name",
            "code",
            "category",
            "department",
            "department_code",
            "description",
            "keywords",
            "x",
            "y",
            "is_wheelchair_accessible",
            "is_landmark",
        ]
