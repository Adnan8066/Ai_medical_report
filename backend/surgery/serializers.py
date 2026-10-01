from rest_framework import serializers

from .models import Surgery


class SurgerySerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    patient_code = serializers.CharField(source="patient.patient_id", read_only=True)
    surgeon_name = serializers.CharField(source="surgeon.name", read_only=True)
    anesthetist_name = serializers.CharField(
        source="anesthetist.name", read_only=True, default=None
    )
    department_name = serializers.CharField(
        source="department.name", read_only=True, default=None
    )
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    anesthesia_label = serializers.CharField(
        source="get_anesthesia_type_display", read_only=True
    )
    nurse_names = serializers.SerializerMethodField()

    class Meta:
        model = Surgery
        fields = [
            "id",
            "surgery_id",
            "patient",
            "patient_name",
            "patient_code",
            "surgeon",
            "surgeon_name",
            "department",
            "department_name",
            "surgery_name",
            "procedure_code",
            "ot_room",
            "date",
            "start_time",
            "end_time",
            "estimated_duration_minutes",
            "anesthetist",
            "anesthetist_name",
            "anesthesia_type",
            "anesthesia_label",
            "nurses",
            "nurse_names",
            "status",
            "status_label",
            "blood_units_reserved",
            "pre_op_notes",
            "post_op_notes",
            "estimated_cost",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["surgery_id", "created_at", "updated_at"]

    def get_nurse_names(self, obj):
        return [nurse.name for nurse in obj.nurses.all()]


class SurgeryWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Surgery
        fields = [
            "id",
            "surgery_id",
            "patient",
            "surgeon",
            "department",
            "surgery_name",
            "procedure_code",
            "ot_room",
            "date",
            "start_time",
            "end_time",
            "estimated_duration_minutes",
            "anesthetist",
            "anesthesia_type",
            "nurses",
            "status",
            "blood_units_reserved",
            "pre_op_notes",
            "post_op_notes",
            "estimated_cost",
        ]
        read_only_fields = ["surgery_id"]

    def validate(self, attrs):
        start = attrs.get("start_time") or getattr(self.instance, "start_time", None)
        end = attrs.get("end_time")
        if start and end and end <= start:
            raise serializers.ValidationError(
                {"end_time": "The end time must be after the start time."}
            )
        surgeon = attrs.get("surgeon") or getattr(self.instance, "surgeon", None)
        if surgeon and not attrs.get("department") and self.instance is None:
            attrs["department"] = surgeon.department

        ot_room = attrs.get("ot_room") or getattr(self.instance, "ot_room", None)
        date_value = attrs.get("date") or getattr(self.instance, "date", None)
        if ot_room and date_value and start and end:
            clashes = Surgery.objects.filter(
                ot_room=ot_room,
                date=date_value,
                status__in=[
                    Surgery.Status.SCHEDULED,
                    Surgery.Status.PREPARING,
                    Surgery.Status.IN_PROGRESS,
                ],
            ).exclude(pk=getattr(self.instance, "pk", None))
            for other in clashes:
                other_end = other.end_time or other.start_time
                if start < other_end and other.start_time < end:
                    raise serializers.ValidationError(
                        {
                            "ot_room": (
                                f"{ot_room} is already booked for {other.surgery_id} "
                                f"({other.start_time:%H:%M}-{other_end:%H:%M})."
                            )
                        }
                    )
        return attrs

    def create(self, validated_data):
        if not validated_data.get("surgery_id"):
            from config.ids import next_sequential_id

            validated_data["surgery_id"] = next_sequential_id(
                Surgery, "surgery_id", "SUR", width=5
            )
        nurses = validated_data.pop("nurses", [])
        surgery = Surgery.objects.create(**validated_data)
        if nurses:
            surgery.nurses.set(nurses)
        return surgery

    def update(self, instance, validated_data):
        nurses = validated_data.pop("nurses", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        if nurses is not None:
            instance.nurses.set(nurses)
        return instance
