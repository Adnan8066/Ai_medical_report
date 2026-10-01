"""Non-doctor staff, shift patterns and rosters."""

from django.conf import settings
from django.db import models


class Shift(models.Model):
    """A named shift pattern such as Morning, Afternoon, Night, Emergency."""

    name = models.CharField(max_length=40, unique=True)
    code = models.CharField(max_length=10, unique=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    description = models.CharField(max_length=200, blank=True)
    is_emergency_shift = models.BooleanField(default=False)
    color = models.CharField(max_length=20, default="#2563eb")

    class Meta:
        ordering = ["start_time"]

    def __str__(self):
        return f"{self.name} ({self.start_time:%H:%M}-{self.end_time:%H:%M})"


class Staff(models.Model):
    class Role(models.TextChoices):
        DOCTOR = "doctor", "Doctor"
        NURSE = "nurse", "Nurse"
        TECHNICIAN = "technician", "Technician"
        PHARMACIST = "pharmacist", "Pharmacist"
        RECEPTIONIST = "receptionist", "Receptionist"
        BILLING = "billing", "Billing Staff"
        ADMINISTRATOR = "administrator", "Administrator"
        HOUSEKEEPING = "housekeeping", "Housekeeping"
        SECURITY = "security", "Security"
        RADIOLOGY = "radiology", "Radiology Technician"
        LABORATORY = "laboratory", "Laboratory Technician"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ON_LEAVE = "on_leave", "On Leave"
        ON_DUTY = "on_duty", "On Duty"
        OFF_DUTY = "off_duty", "Off Duty"
        INACTIVE = "inactive", "Inactive"

    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"

    employee_id = models.CharField(max_length=20, unique=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="staff_profile",
    )
    name = models.CharField(max_length=140)
    gender = models.CharField(max_length=10, choices=Gender.choices, default=Gender.FEMALE)
    department = models.ForeignKey(
        "hospital.Department",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="staff",
    )
    role = models.CharField(max_length=30, choices=Role.choices, default=Role.NURSE)
    designation = models.CharField(max_length=120, blank=True)
    joining_date = models.DateField(null=True, blank=True)
    shift = models.ForeignKey(
        Shift, null=True, blank=True, on_delete=models.SET_NULL, related_name="staff"
    )
    contact = models.CharField(max_length=25, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=250, blank=True)
    qualification = models.CharField(max_length=160, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    is_demo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Staff"
        indexes = [models.Index(fields=["role", "status"]), models.Index(fields=["department"])]

    def __str__(self):
        return f"{self.name} ({self.employee_id})"


class ShiftAssignment(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        ABSENT = "absent", "Absent"
        SWAPPED = "swapped", "Swapped"

    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="shift_assignments")
    shift = models.ForeignKey(Shift, on_delete=models.PROTECT, related_name="assignments")
    date = models.DateField()
    department = models.ForeignKey(
        "hospital.Department",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="shift_assignments",
    )
    ward = models.CharField(max_length=60, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    notes = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "shift__start_time"]
        unique_together = [("staff", "shift", "date")]

    def __str__(self):
        return f"{self.staff.name} - {self.shift.name} on {self.date}"
