"""Inpatient admissions and the discharge workflow."""

from django.conf import settings
from django.db import models


class Admission(models.Model):
    class Status(models.TextChoices):
        ADMITTED = "admitted", "Admitted"
        UNDER_TREATMENT = "under_treatment", "Under Treatment"
        READY_FOR_DISCHARGE = "ready_for_discharge", "Ready for Discharge"
        DISCHARGED = "discharged", "Discharged"
        TRANSFERRED = "transferred", "Transferred"

    admission_id = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="admissions"
    )
    doctor = models.ForeignKey(
        "doctors.Doctor", on_delete=models.PROTECT, related_name="admissions"
    )
    department = models.ForeignKey(
        "hospital.Department",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="admissions",
    )
    admission_date = models.DateTimeField(db_index=True)
    expected_discharge_date = models.DateField(null=True, blank=True)
    discharge_date = models.DateTimeField(null=True, blank=True)
    ward = models.ForeignKey(
        "beds.Ward",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="admissions",
    )
    bed = models.ForeignKey(
        "beds.Bed",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="admissions",
    )
    bed_number = models.CharField(max_length=20, blank=True)
    attending_doctor = models.ForeignKey(
        "doctors.Doctor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="attending_admissions",
    )
    nurse = models.ForeignKey(
        "staff.Staff",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="admissions",
    )
    admission_reason = models.CharField(max_length=300, blank=True)
    diagnosis = models.CharField(max_length=300, blank=True)
    treatment_plan = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.ADMITTED)
    notes = models.TextField(blank=True)
    is_demo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-admission_date"]
        indexes = [models.Index(fields=["status", "department"])]

    def __str__(self):
        return f"{self.admission_id} - {self.patient.name}"

    @property
    def length_of_stay(self):
        end = self.discharge_date
        if end is None:
            from django.utils import timezone

            end = timezone.now()
        return (end - self.admission_date).days


class DischargeSummary(models.Model):
    """Doctor-approved discharge documentation plus the clearance checklist."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING_APPROVAL = "pending_approval", "Pending Doctor Approval"
        APPROVED = "approved", "Approved"
        COMPLETED = "completed", "Completed"

    discharge_id = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="discharge_summaries"
    )
    admission = models.OneToOneField(
        Admission,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="discharge_summary",
    )
    doctor = models.ForeignKey(
        "doctors.Doctor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="discharge_summaries",
    )
    admission_date = models.DateTimeField(null=True, blank=True)
    discharge_date = models.DateTimeField(null=True, blank=True)
    diagnosis_summary = models.TextField(blank=True)
    procedures = models.TextField(blank=True)
    medications = models.TextField(blank=True)
    follow_up_instructions = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True)
    condition_on_discharge = models.CharField(max_length=200, blank=True)
    final_bill = models.ForeignKey(
        "billing.Invoice",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="discharge_summaries",
    )
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.DRAFT)

    # Discharge workflow checklist
    doctor_approved = models.BooleanField(default=False)
    final_bill_settled = models.BooleanField(default=False)
    pharmacy_cleared = models.BooleanField(default=False)
    insurance_processed = models.BooleanField(default=False)
    follow_up_scheduled = models.BooleanField(default=False)

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="discharge_approvals",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    is_demo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Discharge summaries"

    def __str__(self):
        return f"{self.discharge_id} - {self.patient.name}"

    @property
    def workflow_steps(self):
        return [
            {"step": "Doctor approval", "complete": self.doctor_approved},
            {"step": "Discharge summary", "complete": bool(self.diagnosis_summary)},
            {"step": "Final bill", "complete": self.final_bill_settled},
            {"step": "Pharmacy clearance", "complete": self.pharmacy_cleared},
            {"step": "Insurance processing", "complete": self.insurance_processed},
            {"step": "Follow-up appointment", "complete": self.follow_up_scheduled},
            {"step": "Discharged", "complete": self.status == self.Status.COMPLETED},
        ]

    @property
    def workflow_progress(self):
        steps = self.workflow_steps
        return {
            "completed": sum(1 for step in steps if step["complete"]),
            "total": len(steps),
            "percentage": round(
                100 * sum(1 for step in steps if step["complete"]) / len(steps)
            ),
        }
