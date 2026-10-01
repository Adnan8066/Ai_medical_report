from rest_framework import serializers

from .models import InventoryItem, PurchaseOrder, PurchaseOrderItem, StockMovement, Supplier


class SupplierSerializer(serializers.ModelSerializer):
    item_count = serializers.IntegerField(source="items.count", read_only=True)

    class Meta:
        model = Supplier
        fields = [
            "id",
            "name",
            "code",
            "contact_person",
            "phone",
            "email",
            "address",
            "category",
            "tax_id",
            "payment_terms",
            "rating",
            "is_active",
            "item_count",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class InventoryItemSerializer(serializers.ModelSerializer):
    category_label = serializers.CharField(source="get_category_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True, default=None)
    stock_value = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)

    class Meta:
        model = InventoryItem
        fields = [
            "id",
            "item_code",
            "name",
            "category",
            "category_label",
            "description",
            "unit",
            "stock",
            "reorder_level",
            "unit_price",
            "stock_value",
            "supplier",
            "supplier_name",
            "location",
            "batch_number",
            "expiry_date",
            "status",
            "status_label",
            "last_restocked_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["item_code", "created_at", "updated_at"]
        extra_kwargs = {"unit_price": {"required": False}}

    def create(self, validated_data):
        if not validated_data.get("item_code"):
            from config.ids import next_sequential_id

            validated_data["item_code"] = next_sequential_id(
                InventoryItem, "item_code", "INV", width=5
            )
        item = InventoryItem(**validated_data)
        item.status = item.compute_status()
        item.save()
        return item

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.status = (
            InventoryItem.Status.DISCONTINUED
            if instance.status == InventoryItem.Status.DISCONTINUED
            else instance.compute_status()
        )
        instance.save()
        return instance


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.name", read_only=True, default=None)

    class Meta:
        model = PurchaseOrderItem
        fields = [
            "id",
            "item",
            "item_name",
            "description",
            "quantity",
            "received_quantity",
            "unit_price",
            "amount",
        ]
        read_only_fields = ["amount"]


class PurchaseOrderSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    items = PurchaseOrderItemSerializer(many=True, required=False)

    class Meta:
        model = PurchaseOrder
        fields = [
            "id",
            "po_number",
            "supplier",
            "supplier_name",
            "order_date",
            "expected_date",
            "status",
            "status_label",
            "total_amount",
            "notes",
            "items",
            "created_at",
        ]
        read_only_fields = ["po_number", "total_amount", "created_at"]

    def create(self, validated_data):
        items = validated_data.pop("items", [])
        if not validated_data.get("po_number"):
            from config.ids import next_sequential_id

            validated_data["po_number"] = next_sequential_id(
                PurchaseOrder, "po_number", "PO", width=5
            )
        order = PurchaseOrder.objects.create(**validated_data)
        for item in items:
            PurchaseOrderItem.objects.create(purchase_order=order, **item)
        order.recalculate()
        return order

    def update(self, instance, validated_data):
        items = validated_data.pop("items", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        if items is not None:
            instance.items.all().delete()
            for item in items:
                PurchaseOrderItem.objects.create(purchase_order=instance, **item)
        instance.recalculate()
        return instance


class StockMovementSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.name", read_only=True)
    item_code = serializers.CharField(source="item.item_code", read_only=True)
    movement_label = serializers.CharField(source="get_movement_type_display", read_only=True)
    performed_by_name = serializers.CharField(
        source="performed_by.full_name", read_only=True, default=None
    )

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "item",
            "item_name",
            "item_code",
            "movement_type",
            "movement_label",
            "quantity",
            "balance_after",
            "reason",
            "reference",
            "performed_by",
            "performed_by_name",
            "created_at",
        ]
        read_only_fields = ["balance_after", "performed_by", "created_at"]
