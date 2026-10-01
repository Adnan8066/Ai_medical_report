"""Laboratory test catalogue, orders and results."""

from django.conf import settings
from django.db import models


class LabTest(models.Model):
    class Category(models.TextChoices):
        HEMATOLOGY = "hematology", "Hematology"
        BIOCHEMISTRY = "biochemistry", "Biochemistry"
        MICROBIOLOGY = "microbiology", "Microbiology"
        SEROLOGY = "serology", "Serology"
        PATHOLOGY = "pathology", "Pathology"
        URINE = "urine", "Urine Analysis"
        HORMONE = "hormone", "Hormone Assay"
        CARDIAC = "cardiac", "Cardiac Markers"

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=120, unique=True)
    category = models.CharField(
        max_length=30, choices=Category.choices, default=Category.BIOCHEMISTRY
    )
    sample_type = models.CharField(max_length=60, default="Blood")
    unit = models.CharField(max_length=20, blank=True)
    reference_range = models.CharField(max_length=80, blank=True)
    turnaround_hours = models.PositiveSmallIntegerField(default=24)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.CharField(max_length=250, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class LabReport(models.Model):
    class Status(models.TextChoices):
        ORDERED = "ordered", "Ordered"
        SAMPLE_COLLECTED = "sample_collected", "Sample Collected"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class Flag(models.TextChoices):
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"
        LOW = "low", "Low"
        CRITICAL = "critical", "Critical"
        UNKNOWN = "unknown", "Not Evaluated"

    lab_id = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="lab_reports"
    )
    doctor = models.ForeignKey(
        "doctors.Doctor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="lab_orders",
    )
    test = models.ForeignKey(
        LabTest, null=True, blank=True, on_delete=models.SET_NULL, related_name="reports"
    )
    ordered_at = models.DateTimeField(auto_now_add=True)
    sample_collected_at = models.DateTimeField(null=True, blank=True)
    report_date = models.DateTimeField(null=True, blank=True)
    result = models.CharField(max_length=250, blank=True)
    numeric_value = models.DecimalField(
        max_digits=10, decimal_places=3, null=True, blank=True
    )
    unit = models.CharField(max_length=20, blank=True)
    reference_range = models.CharField(max_length=80, blank=True)
    flag = models.CharField(max_length=20, choices=Flag.choices, default=Flag.UNKNOWN)
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.ORDERED)
    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="lab_reports_handled",
    )
    technician_name = models.CharField(max_length=120, blank=True)
    remarks = models.CharField(max_length=250, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_demo = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-ordered_at"]
        indexes = [models.Index(fields=["status"]), models.Index(fields=["patient"])]

    def __str__(self):
        return f"{self.lab_id} - {self.test.name if self.test else 'Test'}"
