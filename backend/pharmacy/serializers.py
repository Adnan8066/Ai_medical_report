from rest_framework import serializers

from .models import Medicine, Prescription, PrescriptionItem


class MedicineSerializer(serializers.ModelSerializer):
    category_label = serializers.CharField(source="get_category_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True, default=None)
    days_to_expiry = serializers.IntegerField(read_only=True)
    stock_value = serializers.SerializerMethodField()

    class Meta:
        model = Medicine
        fields = [
            "id",
            "medicine_id",
            "name",
            "generic_name",
            "category",
            "category_label",
            "manufacturer",
            "batch_number",
            "expiry_date",
            "days_to_expiry",
            "stock",
            "reorder_level",
            "unit",
            "price",
            "cost_price",
            "storage",
            "prescription_required",
            "supplier",
            "supplier_name",
            "status",
            "status_label",
            "stock_value",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["medicine_id", "created_at", "updated_at"]

    def get_stock_value(self, obj):
        return (obj.stock or 0) * (obj.cost_price or 0)


class MedicineWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine
        fields = [
            "id",
            "medicine_id",
            "name",
            "generic_name",
            "category",
            "manufacturer",
            "batch_number",
            "expiry_date",
            "stock",
            "reorder_level",
            "unit",
            "price",
            "cost_price",
            "storage",
            "prescription_required",
            "supplier",
            "status",
        ]
        read_only_fields = ["medicine_id"]

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("Stock cannot be negative.")
        return value

    def create(self, validated_data):
        if not validated_data.get("medicine_id"):
            from config.ids import next_sequential_id

            validated_data["medicine_id"] = next_sequential_id(
                Medicine, "medicine_id", "MED", width=5
            )
        medicine = Medicine(**validated_data)
        medicine.status = medicine.compute_status()
        medicine.save()
        return medicine

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.status = (
            Medicine.Status.DISCONTINUED
            if instance.status == Medicine.Status.DISCONTINUED
            else instance.compute_status()
        )
        instance.save()
        return instance


class PrescriptionItemSerializer(serializers.ModelSerializer):
    medicine_name_display = serializers.CharField(
        source="medicine.name", read_only=True, default=None
    )
    medicine_code = serializers.CharField(
        source="medicine.medicine_id", read_only=True, default=None
    )
    unit_price = serializers.DecimalField(
        source="medicine.price", max_digits=10, decimal_places=2, read_only=True, default=0
    )

    class Meta:
        model = PrescriptionItem
        fields = [
            "id",
            "medicine",
            "medicine_name",
            "medicine_name_display",
            "medicine_code",
            "dosage",
            "frequency",
            "duration",
            "route",
            "quantity",
            "instructions",
            "dispensed",
            "unit_price",
        ]


class PrescriptionSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    patient_code = serializers.CharField(source="patient.patient_id", read_only=True)
    doctor_name = serializers.CharField(source="doctor.name", read_only=True, default=None)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    items = PrescriptionItemSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = Prescription
        fields = [
            "id",
            "prescription_id",
            "patient",
            "patient_name",
            "patient_code",
            "doctor",
            "doctor_name",
            "admission",
            "date",
            "status",
            "status_label",
            "notes",
            "items",
            "total_amount",
            "dispensed_at",
            "created_at",
        ]
        read_only_fields = ["prescription_id", "created_at", "dispensed_at"]


class PrescriptionWriteSerializer(serializers.ModelSerializer):
    items = PrescriptionItemSerializer(many=True, required=False)

    class Meta:
        model = Prescription
        fields = [
            "id",
            "prescription_id",
            "patient",
            "doctor",
            "admission",
            "date",
            "status",
            "notes",
            "items",
        ]
        read_only_fields = ["prescription_id"]

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Add at least one medicine to the prescription.")
        return value

    def create(self, validated_data):
        items = validated_data.pop("items", [])
        if not validated_data.get("prescription_id"):
            from config.ids import next_sequential_id

            validated_data["prescription_id"] = next_sequential_id(
                Prescription, "prescription_id", "RX", width=5
            )
        prescription = Prescription.objects.create(**validated_data)
        for item in items:
            medicine = item.get("medicine")
            PrescriptionItem.objects.create(
                prescription=prescription,
                medicine_name=item.get("medicine_name")
                or (medicine.name if medicine else "Medicine"),
                **{k: v for k, v in item.items() if k not in {"medicine_name"}},
            )
        return prescription

    def update(self, instance, validated_data):
        items = validated_data.pop("items", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        if items is not None:
            instance.items.all().delete()
            for item in items:
                medicine = item.get("medicine")
                PrescriptionItem.objects.create(
                    prescription=instance,
                    medicine_name=item.get("medicine_name")
                    or (medicine.name if medicine else "Medicine"),
                    **{k: v for k, v in item.items() if k not in {"medicine_name"}},
                )
        return instance
