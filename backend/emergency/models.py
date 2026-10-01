"""Emergency department triage and treatment tracking."""

from django.db import models
from django.utils import timezone


class EmergencyVisit(models.Model):
    class Priority(models.TextChoices):
        CRITICAL = "critical", "Critical"
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"

    class Status(models.TextChoices):
        WAITING = "waiting", "Waiting"
        TRIAGED = "triaged", "Triaged"
        IN_TREATMENT = "in_treatment", "In Treatment"
        OBSERVATION = "observation", "Under Observation"
        ADMITTED = "admitted", "Admitted to Ward"
        DISCHARGED = "discharged", "Discharged"
        REFERRED = "referred", "Referred"
        TRANSFERRED = "transferred", "Transferred"

    case_id = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="emergency_visits"
    )
    arrival_time = models.DateTimeField(default=timezone.now, db_index=True)
    triage_time = models.DateTimeField(null=True, blank=True)
    priority = models.CharField(
        max_length=20, choices=Priority.choices, default=Priority.MEDIUM
    )
    assigned_doctor = models.ForeignKey(
        "doctors.Doctor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="emergency_cases",
    )
    assigned_nurse = models.ForeignKey(
        "staff.Staff",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="emergency_cases",
    )
    bed = models.ForeignKey(
        "beds.Bed",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="emergency_cases",
    )
    chief_complaint = models.CharField(max_length=300, blank=True)
    condition_notes = models.TextField(blank=True)
    vitals_summary = models.CharField(max_length=250, blank=True)
    treatment_given = models.TextField(blank=True)
    disposition = models.CharField(max_length=250, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.WAITING)
    closed_at = models.DateTimeField(null=True, blank=True)
    is_demo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-arrival_time"]
        verbose_name = "Emergency visit"
        indexes = [models.Index(fields=["priority", "status"])]

    def __str__(self):
        return f"{self.case_id} - {self.patient.name} ({self.get_priority_display()})"

    @property
    def waiting_minutes(self):
        """Minutes since arrival (or total time in the department if closed)."""
        end = self.closed_at or timezone.now()
        return max(0, int((end - self.arrival_time).total_seconds() // 60))
