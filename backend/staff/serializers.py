from rest_framework import serializers

from .models import Shift, ShiftAssignment, Staff


class ShiftSerializer(serializers.ModelSerializer):
    duration_hours = serializers.SerializerMethodField()
    staff_on_duty = serializers.SerializerMethodField()

    class Meta:
        model = Shift
        fields = [
            "id",
            "name",
            "code",
            "start_time",
            "end_time",
            "description",
            "is_emergency_shift",
            "color",
            "duration_hours",
            "staff_on_duty",
        ]

    def get_duration_hours(self, obj):
        start = obj.start_time.hour * 60 + obj.start_time.minute
        end = obj.end_time.hour * 60 + obj.end_time.minute
        minutes = (end - start) % (24 * 60)
        return round(minutes / 60, 1)

    def get_staff_on_duty(self, obj):
        return obj.staff.count()


class StaffSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True, default=None)
    role_label = serializers.CharField(source="get_role_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    shift_name = serializers.CharField(source="shift.name", read_only=True, default=None)
    shift_timing = serializers.SerializerMethodField()

    class Meta:
        model = Staff
        fields = [
            "id",
            "employee_id",
            "name",
            "gender",
            "department",
            "department_name",
            "role",
            "role_label",
            "designation",
            "joining_date",
            "shift",
            "shift_name",
            "shift_timing",
            "contact",
            "email",
            "address",
            "qualification",
            "status",
            "status_label",
            "is_demo",
            "created_at",
        ]
        read_only_fields = ["created_at", "is_demo"]

    def get_shift_timing(self, obj):
        if not obj.shift:
            return None
        return f"{obj.shift.start_time:%H:%M} - {obj.shift.end_time:%H:%M}"


class ShiftAssignmentSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source="staff.name", read_only=True)
    staff_role = serializers.CharField(source="staff.get_role_display", read_only=True)
    employee_id = serializers.CharField(source="staff.employee_id", read_only=True)
    shift_name = serializers.CharField(source="shift.name", read_only=True)
    shift_timing = serializers.SerializerMethodField()
    department_name = serializers.CharField(source="department.name", read_only=True, default=None)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = ShiftAssignment
        fields = [
            "id",
            "staff",
            "staff_name",
            "employee_id",
            "staff_role",
            "shift",
            "shift_name",
            "shift_timing",
            "date",
            "department",
            "department_name",
            "ward",
            "status",
            "status_label",
            "notes",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def get_shift_timing(self, obj):
        return f"{obj.shift.start_time:%H:%M} - {obj.shift.end_time:%H:%M}"
