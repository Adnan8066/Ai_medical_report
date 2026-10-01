"""Doctor registry."""

from django.conf import settings
from django.db import models


class Doctor(models.Model):
    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ON_LEAVE = "on_leave", "On Leave"
        INACTIVE = "inactive", "Inactive"

    class Availability(models.TextChoices):
        AVAILABLE = "available", "Available"
        IN_CONSULTATION = "in_consultation", "In Consultation"
        IN_SURGERY = "in_surgery", "In Surgery"
        ON_ROUNDS = "on_rounds", "On Rounds"
        OFF_DUTY = "off_duty", "Off Duty"
        ON_LEAVE = "on_leave", "On Leave"

    class Designation(models.TextChoices):
        HOD = "hod", "HOD & Senior Consultant"
        SENIOR_CONSULTANT = "senior_consultant", "Senior Consultant"
        CONSULTANT = "consultant", "Consultant"
        ASSOCIATE_CONSULTANT = "associate_consultant", "Associate Consultant"
        REGISTRAR = "registrar", "Registrar"
        RESIDENT = "resident", "Resident Medical Officer"
        VISITING = "visiting", "Visiting Consultant"

    doctor_id = models.CharField(max_length=20, unique=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="doctor_profile",
    )
    name = models.CharField(max_length=140)
    gender = models.CharField(max_length=10, choices=Gender.choices, default=Gender.MALE)
    photo = models.ImageField(upload_to="doctors/", null=True, blank=True)
    department = models.ForeignKey(
        "hospital.Department", on_delete=models.PROTECT, related_name="doctors"
    )
    designation = models.CharField(
        max_length=40, choices=Designation.choices, default=Designation.CONSULTANT
    )
    is_hod = models.BooleanField(default=False)
    qualification = models.CharField(max_length=200)
    experience_years = models.PositiveSmallIntegerField(default=0)
    specialization = models.CharField(max_length=200, blank=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    room_number = models.CharField(max_length=20, blank=True)
    phone_extension = models.CharField(max_length=12, blank=True)
    phone = models.CharField(max_length=25, blank=True)
    email = models.EmailField(blank=True)
    availability = models.CharField(
        max_length=20, choices=Availability.choices, default=Availability.AVAILABLE
    )
    available_days = models.CharField(max_length=120, blank=True)
    opd_schedule = models.JSONField(
        default=dict,
        blank=True,
        help_text="Weekday -> list of consultation slots, e.g. {'mon': ['09:00-13:00']}",
    )
    joining_date = models.DateField(null=True, blank=True)
    languages = models.CharField(max_length=120, blank=True)
    about = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    is_demo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["department", "status"])]

    def __str__(self):
        return f"{self.name} ({self.doctor_id})"

    @property
    def short_name(self):
        return self.name.replace("Dr. ", "Dr ")
