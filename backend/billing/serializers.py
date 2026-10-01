from rest_framework import serializers

from .models import Invoice, InvoiceItem


class InvoiceItemSerializer(serializers.ModelSerializer):
    service_label = serializers.CharField(source="get_service_type_display", read_only=True)

    class Meta:
        model = InvoiceItem
        fields = [
            "id",
            "service_type",
            "service_label",
            "description",
            "quantity",
            "unit_price",
            "amount",
        ]
        read_only_fields = ["amount"]


class InvoiceSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.name", read_only=True)
    patient_code = serializers.CharField(source="patient.patient_id", read_only=True)
    doctor_name = serializers.CharField(source="doctor.name", read_only=True, default=None)
    status_label = serializers.CharField(source="get_payment_status_display", read_only=True)
    payment_method_label = serializers.CharField(
        source="get_payment_method_display", read_only=True
    )
    items = InvoiceItemSerializer(many=True, read_only=True)
    balance_due = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "patient",
            "patient_name",
            "patient_code",
            "admission",
            "doctor",
            "doctor_name",
            "date",
            "subtotal",
            "discount",
            "tax_rate",
            "tax_amount",
            "insurance_amount",
            "patient_payable",
            "paid_amount",
            "balance_due",
            "payment_status",
            "status_label",
            "payment_method",
            "payment_method_label",
            "notes",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "invoice_number",
            "subtotal",
            "tax_amount",
            "patient_payable",
            "created_at",
            "updated_at",
        ]


class InvoiceWriteSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, required=False)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "invoice_number",
            "patient",
            "admission",
            "doctor",
            "date",
            "discount",
            "tax_rate",
            "insurance_amount",
            "paid_amount",
            "payment_status",
            "payment_method",
            "notes",
            "items",
        ]
        read_only_fields = ["invoice_number"]

    def validate(self, attrs):
        insurance_amount = attrs.get("insurance_amount")
        if insurance_amount is not None and insurance_amount < 0:
            raise serializers.ValidationError(
                {"insurance_amount": "The insurance amount cannot be negative."}
            )
        items = attrs.get("items")
        if items is not None and not items and self.instance is None:
            raise serializers.ValidationError(
                {"items": "Add at least one billable service to the invoice."}
            )
        return attrs

    def _write_items(self, invoice, items):
        invoice.items.all().delete()
        for item in items:
            InvoiceItem.objects.create(invoice=invoice, **item)

    def create(self, validated_data):
        items = validated_data.pop("items", [])
        if not validated_data.get("invoice_number"):
            from config.ids import next_sequential_id

            validated_data["invoice_number"] = next_sequential_id(
                Invoice, "invoice_number", "INV", width=5
            )
        invoice = Invoice.objects.create(**validated_data)
        self._write_items(invoice, items)
        invoice.recalculate()
        return invoice

    def update(self, instance, validated_data):
        items = validated_data.pop("items", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        if items is not None:
            self._write_items(instance, items)
        instance.recalculate()
        return instance
