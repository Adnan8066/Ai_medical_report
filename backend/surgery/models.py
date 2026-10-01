"""Operation theatre scheduling."""

from django.db import models


class Surgery(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        PREPARING = "preparing", "Preparing"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        POSTPONED = "postponed", "Postponed"

    class AnesthesiaType(models.TextChoices):
        GENERAL = "general", "General"
        SPINAL = "spinal", "Spinal"
        EPIDURAL = "epidural", "Epidural"
        REGIONAL = "regional", "Regional Block"
        LOCAL = "local", "Local"
        SEDATION = "sedation", "Conscious Sedation"

    surgery_id = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="surgeries"
    )
    surgeon = models.ForeignKey(
        "doctors.Doctor",
        on_delete=models.PROTECT,
        related_name="surgeries_performed",
    )
    department = models.ForeignKey(
        "hospital.Department",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="surgeries",
    )
    surgery_name = models.CharField(max_length=200)
    procedure_code = models.CharField(max_length=30, blank=True)
    ot_room = models.CharField(max_length=30)
    date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    estimated_duration_minutes = models.PositiveIntegerField(default=60)
    anesthetist = models.ForeignKey(
        "doctors.Doctor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="anesthesia_cases",
    )
    anesthesia_type = models.CharField(
        max_length=20, choices=AnesthesiaType.choices, default=AnesthesiaType.GENERAL
    )
    nurses = models.ManyToManyField(
        "staff.Staff", blank=True, related_name="surgery_assists"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    blood_units_reserved = models.PositiveSmallIntegerField(default=0)
    pre_op_notes = models.TextField(blank=True)
    post_op_notes = models.TextField(blank=True)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_demo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "start_time"]
        verbose_name_plural = "Surgeries"
        indexes = [models.Index(fields=["date", "status"])]

    def __str__(self):
        return f"{self.surgery_id} - {self.surgery_name}"
