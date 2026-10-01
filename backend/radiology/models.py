"""Imaging and diagnostic studies."""

from django.conf import settings
from django.db import models


class RadiologyReport(models.Model):
    class ScanType(models.TextChoices):
        XRAY = "xray", "X-Ray"
        CT = "ct", "CT Scan"
        MRI = "mri", "MRI"
        ULTRASOUND = "ultrasound", "Ultrasound"
        ECG = "ecg", "ECG"
        ECHO = "echo", "Echocardiography"
        MAMMOGRAPHY = "mammography", "Mammography"
        PET = "pet", "PET Scan"

    class Status(models.TextChoices):
        ORDERED = "ordered", "Ordered"
        SCHEDULED = "scheduled", "Scheduled"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    scan_id = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="radiology_studies"
    )
    doctor = models.ForeignKey(
        "doctors.Doctor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="radiology_orders",
    )
    scan_type = models.CharField(max_length=20, choices=ScanType.choices)
    body_part = models.CharField(max_length=80, blank=True)
    appointment_date = models.DateTimeField(null=True, blank=True)
    radiologist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="radiology_reports",
    )
    radiologist_name = models.CharField(max_length=120, blank=True)
    technician_name = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ORDERED)
    findings = models.TextField(blank=True)
    impression = models.CharField(max_length=300, blank=True)
    report = models.TextField(blank=True)
    report_date = models.DateTimeField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_demo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-appointment_date", "-created_at"]
        indexes = [models.Index(fields=["status", "scan_type"])]

    def __str__(self):
        return f"{self.scan_id} - {self.get_scan_type_display()} for {self.patient.name}"
