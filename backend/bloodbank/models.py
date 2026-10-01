"""Blood bank inventory, donations and issues."""

from django.conf import settings
from django.db import models


BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]


class BloodStock(models.Model):
    blood_group = models.CharField(max_length=5, unique=True, choices=[(g, g) for g in BLOOD_GROUPS])
    units_available = models.PositiveIntegerField(default=0)
    units_reserved = models.PositiveIntegerField(default=0)
    critical_threshold = models.PositiveIntegerField(default=5)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["blood_group"]
        verbose_name_plural = "Blood stock"

    def __str__(self):
        return f"{self.blood_group}: {self.units_available} units"

    @property
    def status(self):
        if self.units_available <= 0:
            return "out_of_stock"
        if self.units_available <= self.critical_threshold:
            return "critical"
        if self.units_available <= self.critical_threshold * 2:
            return "low"
        return "adequate"

    @property
    def total_units(self):
        return self.units_available + self.units_reserved


class Donation(models.Model):
    class Screening(models.TextChoices):
        PENDING = "pending", "Pending"
        PASSED = "passed", "Screening Passed"
        FAILED = "failed", "Screening Failed"

    donation_id = models.CharField(max_length=20, unique=True)
    donor_name = models.CharField(max_length=140)
    donor_code = models.CharField(max_length=20, blank=True)
    blood_group = models.CharField(max_length=5, choices=[(g, g) for g in BLOOD_GROUPS])
    units = models.PositiveSmallIntegerField(default=1)
    donation_date = models.DateField(db_index=True)
    donor_age = models.PositiveSmallIntegerField(null=True, blank=True)
    donor_gender = models.CharField(max_length=10, blank=True)
    donor_phone = models.CharField(max_length=20, blank=True)
    camp_location = models.CharField(max_length=140, blank=True)
    screening = models.CharField(
        max_length=20, choices=Screening.choices, default=Screening.PASSED
    )
    hemoglobin = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    notes = models.CharField(max_length=250, blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="donations_recorded",
    )
    is_demo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-donation_date"]

    def __str__(self):
        return f"{self.donation_id} - {self.donor_name} ({self.blood_group})"


class BloodIssue(models.Model):
    class Status(models.TextChoices):
        RESERVED = "reserved", "Reserved"
        ISSUED = "issued", "Issued"
        TRANSFUSED = "transfused", "Transfused"
        RETURNED = "returned", "Returned"
        DISCARDED = "discarded", "Discarded"

    issue_id = models.CharField(max_length=20, unique=True)
    blood_group = models.CharField(max_length=5, choices=[(g, g) for g in BLOOD_GROUPS])
    units = models.PositiveSmallIntegerField(default=1)
    patient = models.ForeignKey(
        "patients.Patient",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="blood_issues",
    )
    ward = models.CharField(max_length=80, blank=True)
    reason = models.CharField(max_length=200, blank=True)
    crossmatch_id = models.CharField(max_length=40, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    issued_at = models.DateTimeField(null=True, blank=True)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="blood_issued",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RESERVED)
    notes = models.CharField(max_length=250, blank=True)
    is_demo = models.BooleanField(default=True)

    class Meta:
        ordering = ["-requested_at"]

    def __str__(self):
        return f"{self.issue_id} - {self.blood_group} x{self.units}"
