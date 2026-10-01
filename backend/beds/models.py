"""Wards, beds and live occupancy."""

from django.db import models


class Ward(models.Model):
    class Category(models.TextChoices):
        GENERAL = "general", "General Ward"
        SEMI_PRIVATE = "semi_private", "Semi-Private"
        PRIVATE = "private", "Private"
        ICU = "icu", "ICU"
        EMERGENCY = "emergency", "Emergency"
        PEDIATRIC = "pediatric", "Pediatric"
        MATERNITY = "maternity", "Maternity"
        ISOLATION = "isolation", "Isolation"

    name = models.CharField(max_length=80, unique=True)
    code = models.CharField(max_length=12, unique=True)
    department = models.ForeignKey(
        "hospital.Department",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="wards",
    )
    floor = models.CharField(max_length=40, blank=True)
    category = models.CharField(
        max_length=20, choices=Category.choices, default=Category.GENERAL
    )
    description = models.CharField(max_length=250, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Bed(models.Model):
    class Category(models.TextChoices):
        GENERAL = "general", "General Ward"
        SEMI_PRIVATE = "semi_private", "Semi-Private"
        PRIVATE = "private", "Private"
        ICU = "icu", "ICU"
        EMERGENCY = "emergency", "Emergency"
        PEDIATRIC = "pediatric", "Pediatric"
        MATERNITY = "maternity", "Maternity"
        ISOLATION = "isolation", "Isolation"

    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        OCCUPIED = "occupied", "Occupied"
        RESERVED = "reserved", "Reserved"
        MAINTENANCE = "maintenance", "Under Maintenance"
        CLEANING = "cleaning", "Cleaning"

    bed_number = models.CharField(max_length=20, unique=True)
    ward = models.ForeignKey(
        Ward, null=True, blank=True, on_delete=models.SET_NULL, related_name="beds"
    )
    department = models.ForeignKey(
        "hospital.Department",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="beds",
    )
    category = models.CharField(
        max_length=20, choices=Category.choices, default=Category.GENERAL
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.AVAILABLE, db_index=True
    )
    floor = models.CharField(max_length=40, blank=True)
    room_number = models.CharField(max_length=20, blank=True)
    patient = models.ForeignKey(
        "patients.Patient",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="current_beds",
    )
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    has_oxygen = models.BooleanField(default=True)
    has_ventilator = models.BooleanField(default=False)
    is_monitored = models.BooleanField(default=False)
    notes = models.CharField(max_length=250, blank=True)
    last_cleaned_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["bed_number"]
        indexes = [models.Index(fields=["status", "category"])]

    def __str__(self):
        return f"{self.bed_number} ({self.get_status_display()})"
