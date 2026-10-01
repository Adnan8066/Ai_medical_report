"""OPD (outpatient department) consultation records."""

from django.db import models


class OPDVisit(models.Model):
    class Status(models.TextChoices):
        WAITING = "waiting", "Waiting"
        IN_CONSULTATION = "in_consultation", "In Consultation"
        COMPLETED = "completed", "Completed"
        REFERRED = "referred", "Referred"
        FOLLOW_UP_REQUIRED = "follow_up_required", "Follow-up Required"
        CANCELLED = "cancelled", "Cancelled"

    visit_id = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="opd_visits"
    )
    doctor = models.ForeignKey(
        "doctors.Doctor", on_delete=models.PROTECT, related_name="opd_visits"
    )
    department = models.ForeignKey(
        "hospital.Department",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="opd_visits",
    )
    appointment = models.OneToOneField(
        "appointments.Appointment",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="opd_visit",
    )
    visit_date = models.DateField(db_index=True)
    visit_time = models.TimeField(null=True, blank=True)
    chief_complaint = models.CharField(max_length=300, blank=True)
    symptoms = models.TextField(blank=True)
    consultation_notes = models.TextField(blank=True)
    diagnosis = models.CharField(max_length=300, blank=True)
    prescription_notes = models.TextField(
        blank=True, help_text="Free-text prescription recorded during the consultation."
    )
    advice = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.WAITING)
    is_demo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-visit_date", "-visit_time"]
        verbose_name = "OPD visit"

    def __str__(self):
        return f"{self.visit_id} - {self.patient.name}"
