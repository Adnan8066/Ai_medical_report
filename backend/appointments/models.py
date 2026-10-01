"""Outpatient appointment scheduling."""

from django.conf import settings
from django.db import models


class Appointment(models.Model):
    class AppointmentType(models.TextChoices):
        CONSULTATION = "consultation", "Consultation"
        FOLLOW_UP = "follow_up", "Follow-up"
        PROCEDURE = "procedure", "Procedure"
        DIAGNOSTIC = "diagnostic", "Diagnostic"
        VACCINATION = "vaccination", "Vaccination"
        EMERGENCY = "emergency", "Emergency"
        TELECONSULTATION = "teleconsultation", "Teleconsultation"

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        CONFIRMED = "confirmed", "Confirmed"
        IN_CONSULTATION = "in_consultation", "In Consultation"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        NO_SHOW = "no_show", "No Show"

    appointment_id = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="appointments"
    )
    doctor = models.ForeignKey(
        "doctors.Doctor", on_delete=models.PROTECT, related_name="appointments"
    )
    department = models.ForeignKey(
        "hospital.Department",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="appointments",
    )
    date = models.DateField(db_index=True)
    time = models.TimeField()
    appointment_type = models.CharField(
        max_length=20, choices=AppointmentType.choices, default=AppointmentType.CONSULTATION
    )
    reason = models.CharField(max_length=250, blank=True)
    notes = models.TextField(blank=True)
    token_number = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    reminder_sent = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="appointments_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_demo = models.BooleanField(default=True)

    class Meta:
        ordering = ["-date", "time"]
        indexes = [
            models.Index(fields=["date", "status"]),
            models.Index(fields=["doctor", "date"]),
        ]

    def __str__(self):
        return f"{self.appointment_id} - {self.patient.name} with {self.doctor.name}"
