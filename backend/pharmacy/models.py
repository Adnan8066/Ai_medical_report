"""Pharmacy stock and prescriptions."""

from datetime import date

from django.conf import settings
from django.db import models


class Medicine(models.Model):
    class Category(models.TextChoices):
        ANTIBIOTIC = "antibiotic", "Antibiotic"
        ANALGESIC = "analgesic", "Analgesic"
        CARDIOVASCULAR = "cardiovascular", "Cardiovascular"
        ANTIDIABETIC = "antidiabetic", "Antidiabetic"
        RESPIRATORY = "respiratory", "Respiratory"
        GASTROINTESTINAL = "gastrointestinal", "Gastrointestinal"
        NEUROLOGICAL = "neurological", "Neurological"
        VITAMIN = "vitamin", "Vitamin / Supplement"
        VACCINE = "vaccine", "Vaccine"
        IV_FLUID = "iv_fluid", "IV Fluid"
        TOPICAL = "topical", "Topical"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        LOW_STOCK = "low_stock", "Low Stock"
        OUT_OF_STOCK = "out_of_stock", "Out of Stock"
        EXPIRING_SOON = "expiring_soon", "Expiring Soon"
        EXPIRED = "expired", "Expired"
        DISCONTINUED = "discontinued", "Discontinued"

    medicine_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=140)
    generic_name = models.CharField(max_length=140, blank=True)
    category = models.CharField(
        max_length=30, choices=Category.choices, default=Category.OTHER
    )
    manufacturer = models.CharField(max_length=140, blank=True)
    batch_number = models.CharField(max_length=40, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=20)
    unit = models.CharField(max_length=20, default="tablet")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    storage = models.CharField(max_length=80, blank=True, default="Room temperature")
    prescription_required = models.BooleanField(default=True)
    supplier = models.ForeignKey(
        "inventory.Supplier",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="medicines",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.AVAILABLE
    )
    is_demo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Medicines"
        indexes = [models.Index(fields=["status"]), models.Index(fields=["category"])]

    def __str__(self):
        return f"{self.name} ({self.medicine_id})"

    @property
    def days_to_expiry(self):
        if not self.expiry_date:
            return None
        return (self.expiry_date - date.today()).days

    def compute_status(self):
        """Derive the display status from live stock and expiry data."""
        if self.status == self.Status.DISCONTINUED:
            return self.Status.DISCONTINUED
        today = date.today()
        if self.expiry_date and self.expiry_date < today:
            return self.Status.EXPIRED
        if self.stock == 0:
            return self.Status.OUT_OF_STOCK
        if self.stock <= self.reorder_level:
            return self.Status.LOW_STOCK
        if self.expiry_date and (self.expiry_date - today).days <= 90:
            return self.Status.EXPIRING_SOON
        return self.Status.AVAILABLE


class Prescription(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PARTIALLY_DISPENSED = "partially_dispensed", "Partially Dispensed"
        DISPENSED = "dispensed", "Dispensed"
        CANCELLED = "cancelled", "Cancelled"

    prescription_id = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="prescriptions"
    )
    doctor = models.ForeignKey(
        "doctors.Doctor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="prescriptions",
    )
    admission = models.ForeignKey(
        "admissions.Admission",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="prescriptions",
    )
    date = models.DateField(default=date.today)
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True)
    dispensed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="prescriptions_dispensed",
    )
    dispensed_at = models.DateTimeField(null=True, blank=True)
    is_demo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.prescription_id} - {self.patient.name}"

    @property
    def total_amount(self):
        return sum(
            (item.quantity or 0) * (item.medicine.price if item.medicine else 0)
            for item in self.items.all()
        )


class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(
        Prescription, on_delete=models.CASCADE, related_name="items"
    )
    medicine = models.ForeignKey(
        Medicine, null=True, blank=True, on_delete=models.SET_NULL, related_name="items"
    )
    medicine_name = models.CharField(max_length=140)
    dosage = models.CharField(max_length=80, blank=True)
    frequency = models.CharField(max_length=80, blank=True)
    duration = models.CharField(max_length=60, blank=True)
    route = models.CharField(max_length=40, blank=True, default="Oral")
    quantity = models.PositiveIntegerField(default=1)
    instructions = models.CharField(max_length=200, blank=True)
    dispensed = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.medicine_name} x{self.quantity}"
