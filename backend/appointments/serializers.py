from rest_framework import serializers

from .models import Appointment


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    patient_code = serializers.CharField(source="patient.patient_id", read_only=True)
    doctor_name = serializers.CharField(source="doctor.name", read_only=True)
    doctor_specialization = serializers.CharField(
        source="doctor.specialization", read_only=True
    )
    department_name = serializers.CharField(
        source="department.name", read_only=True, default=None
    )
    appointment_type_label = serializers.CharField(
        source="get_appointment_type_display", read_only=True
    )
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "appointment_id",
            "patient",
            "patient_name",
            "patient_code",
            "doctor",
            "doctor_name",
            "doctor_specialization",
            "department",
            "department_name",
            "date",
            "time",
            "appointment_type",
            "appointment_type_label",
            "reason",
            "notes",
            "token_number",
            "status",
            "status_label",
            "reminder_sent",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["appointment_id", "created_at", "updated_at"]


class AppointmentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = [
            "id",
            "appointment_id",
            "patient",
            "doctor",
            "department",
            "date",
            "time",
            "appointment_type",
            "reason",
            "notes",
            "token_number",
            "status",
            "reminder_sent",
        ]
        read_only_fields = ["appointment_id"]

    def validate(self, attrs):
        doctor = attrs.get("doctor") or getattr(self.instance, "doctor", None)
        department = attrs.get("department") or getattr(self.instance, "department", None)
        date_value = attrs.get("date") or getattr(self.instance, "date", None)
        time_value = attrs.get("time") or getattr(self.instance, "time", None)

        if doctor and department and doctor.department_id != department.id:
            raise serializers.ValidationError(
                {
                    "department": (
                        f"{doctor.name} practises in {doctor.department.name}. "
                        f"Choose that department or pick another doctor."
                    )
                }
            )

        if doctor and date_value and time_value:
            clash = Appointment.objects.filter(
                doctor=doctor, date=date_value, time=time_value
            ).exclude(status__in=[Appointment.Status.CANCELLED, Appointment.Status.NO_SHOW])
            if self.instance is not None:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                raise serializers.ValidationError(
                    {
                        "time": (
                            f"{doctor.name} already has an appointment at "
                            f"{time_value:%H:%M} on {date_value}. Pick a different slot."
                        )
                    }
                )
        return attrs

    def create(self, validated_data):
        if not validated_data.get("appointment_id"):
            from config.ids import next_sequential_id

            validated_data["appointment_id"] = next_sequential_id(
                Appointment, "appointment_id", "APT"
            )
        if validated_data.get("department") is None and validated_data.get("doctor"):
            validated_data["department"] = validated_data["doctor"].department
        return super().create(validated_data)
