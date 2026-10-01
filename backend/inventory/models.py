"""Suppliers, stock items, purchase orders and stock movements."""

from datetime import date

from django.conf import settings
from django.db import models


class Supplier(models.Model):
    name = models.CharField(max_length=140, unique=True)
    code = models.CharField(max_length=20, unique=True)
    contact_person = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=250, blank=True)
    category = models.CharField(max_length=80, blank=True)
    tax_id = models.CharField(max_length=40, blank=True)
    payment_terms = models.CharField(max_length=80, blank=True, default="Net 30")
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.0)
    is_active = models.BooleanField(default=True)
    is_demo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    class Category(models.TextChoices):
        MEDICAL_EQUIPMENT = "medical_equipment", "Medical Equipment"
        SURGICAL_SUPPLIES = "surgical_supplies", "Surgical Supplies"
        PPE = "ppe", "PPE"
        LABORATORY_SUPPLIES = "laboratory_supplies", "Laboratory Supplies"
        MEDICINES = "medicines", "Medicines"
        OFFICE_SUPPLIES = "office_supplies", "Office Supplies"
        HOUSEKEEPING = "housekeeping", "Housekeeping"
        IT_EQUIPMENT = "it_equipment", "IT Equipment"

    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        LOW_STOCK = "low_stock", "Low Stock"
        OUT_OF_STOCK = "out_of_stock", "Out of Stock"
        EXPIRING_SOON = "expiring_soon", "Expiring Soon"
        EXPIRED = "expired", "Expired"
        DISCONTINUED = "discontinued", "Discontinued"

    item_code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=160)
    category = models.CharField(
        max_length=30, choices=Category.choices, default=Category.SURGICAL_SUPPLIES
    )
    description = models.CharField(max_length=250, blank=True)
    unit = models.CharField(max_length=20, default="unit")
    stock = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=20)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    supplier = models.ForeignKey(
        Supplier, null=True, blank=True, on_delete=models.SET_NULL, related_name="items"
    )
    location = models.CharField(max_length=80, blank=True)
    batch_number = models.CharField(max_length=40, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    last_restocked_at = models.DateTimeField(null=True, blank=True)
    is_demo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["category", "status"])]

    def __str__(self):
        return f"{self.name} ({self.item_code})"

    @property
    def stock_value(self):
        return (self.stock or 0) * (self.unit_price or 0)

    def compute_status(self):
        if self.status == self.Status.DISCONTINUED:
            return self.Status.DISCONTINUED
        today = date.today()
        if self.expiry_date and self.expiry_date < today:
            return self.Status.EXPIRED
        if self.stock == 0:
            return self.Status.OUT_OF_STOCK
        if self.stock <= self.reorder_level:
            return self.Status.LOW_STOCK
        if self.expiry_date and (self.expiry_date - today).days <= 60:
            return self.Status.EXPIRING_SOON
        return self.Status.AVAILABLE


class PurchaseOrder(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        APPROVED = "approved", "Approved"
        PARTIALLY_RECEIVED = "partially_received", "Partially Received"
        RECEIVED = "received", "Received"
        CANCELLED = "cancelled", "Cancelled"

    po_number = models.CharField(max_length=20, unique=True)
    supplier = models.ForeignKey(
        Supplier, on_delete=models.PROTECT, related_name="purchase_orders"
    )
    order_date = models.DateField(default=date.today)
    expected_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.DRAFT)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.CharField(max_length=250, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="purchase_orders",
    )
    is_demo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-order_date"]

    def __str__(self):
        return f"{self.po_number} - {self.supplier.name}"

    def recalculate(self):
        total = sum((item.amount or 0) for item in self.items.all())
        self.total_amount = total
        self.save(update_fields=["total_amount"])
        return total


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(
        PurchaseOrder, on_delete=models.CASCADE, related_name="items"
    )
    item = models.ForeignKey(
        InventoryItem, null=True, blank=True, on_delete=models.SET_NULL, related_name="po_items"
    )
    description = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    received_quantity = models.PositiveIntegerField(default=0)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.description} x{self.quantity}"

    def save(self, *args, **kwargs):
        self.amount = (self.unit_price or 0) * (self.quantity or 0)
        super().save(*args, **kwargs)


class StockMovement(models.Model):
    class MovementType(models.TextChoices):
        IN = "in", "Stock In"
        OUT = "out", "Stock Out"
        ADJUSTMENT = "adjustment", "Adjustment"
        RETURN = "return", "Return"
        DISPOSAL = "disposal", "Disposal"

    item = models.ForeignKey(
        InventoryItem, on_delete=models.CASCADE, related_name="movements"
    )
    movement_type = models.CharField(max_length=20, choices=MovementType.choices)
    quantity = models.IntegerField()
    balance_after = models.IntegerField(default=0)
    reason = models.CharField(max_length=200, blank=True)
    reference = models.CharField(max_length=60, blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="stock_movements",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_movement_type_display()} {self.quantity} - {self.item.name}"
