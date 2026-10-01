"""Patient master index, vitals and nursing assignments."""

from datetime import date

from django.conf import settings
from django.db import models


class Patient(models.Model):
    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"

    class BloodGroup(models.TextChoices):
        A_POS = "A+", "A+"
        A_NEG = "A-", "A-"
        B_POS = "B+", "B+"
        B_NEG = "B-", "B-"
        AB_POS = "AB+", "AB+"
        AB_NEG = "AB-", "AB-"
        O_POS = "O+", "O+"
        O_NEG = "O-", "O-"

    class PatientType(models.TextChoices):
        OPD = "opd", "OPD"
        OUTPATIENT = "outpatient", "Outpatient"
        INPATIENT = "inpatient", "Inpatient"
        EMERGENCY = "emergency", "Emergency"
        ICU = "icu", "ICU"
        DISCHARGED = "discharged", "Discharged"
        FOLLOW_UP = "follow_up", "Follow-up"
        SCHEDULED = "scheduled", "Scheduled Appointment"

    class Status(models.TextChoices):
        REGISTERED = "registered", "Registered"
        WAITING = "waiting", "Waiting"
        IN_CONSULTATION = "in_consultation", "In Consultation"
        ADMITTED = "admitted", "Admitted"
        UNDER_TREATMENT = "under_treatment", "Under Treatment"
        STABLE = "stable", "Stable"
        CRITICAL = "critical", "Critical"
        READY_FOR_DISCHARGE = "ready_for_discharge", "Ready for Discharge"
        DISCHARGED = "discharged", "Discharged"
        FOLLOW_UP = "follow_up", "Follow-up"

    class AdmissionStatus(models.TextChoices):
        NOT_ADMITTED = "not_admitted", "Not Admitted"
        ADMITTED = "admitted", "Admitted"
        DISCHARGED = "discharged", "Discharged"

    patient_id = models.CharField(max_length=20, unique=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="patient_profile",
    )
    name = models.CharField(max_length=140)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, default=Gender.MALE)
    blood_group = models.CharField(max_length=5, choices=BloodGroup.choices, blank=True)
    photo = models.ImageField(upload_to="patients/", null=True, blank=True)
    phone = models.CharField(max_length=25, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=250, blank=True)
    city = models.CharField(max_length=80, blank=True)
    state = models.CharField(max_length=80, blank=True)
    postal_code = models.CharField(max_length=12, blank=True)
    emergency_contact_name = models.CharField(max_length=140, blank=True)
    emergency_contact_phone = models.CharField(max_length=25, blank=True)
    emergency_contact_relation = models.CharField(max_length=60, blank=True)
    department = models.ForeignKey(
        "hospital.Department",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="patients",
    )
    assigned_doctor = models.ForeignKey(
        "doctors.Doctor",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="patients",
    )
    registration_date = models.DateField(default=date.today)
    patient_type = models.CharField(
        max_length=20, choices=PatientType.choices, default=PatientType.OPD
    )
    current_status = models.CharField(
        max_length=30, choices=Status.choices, default=Status.REGISTERED
    )
    admission_status = models.CharField(
        max_length=20,
        choices=AdmissionStatus.choices,
        default=AdmissionStatus.NOT_ADMITTED,
    )
    allergies = models.CharField(
        max_length=250, blank=True, help_text="Comma separated list of known allergies."
    )
    medical_history = models.TextField(blank=True)
    chronic_conditions = models.CharField(max_length=250, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    insurance_provider = models.CharField(max_length=120, blank=True)
    insurance_policy_number = models.CharField(max_length=60, blank=True)
    notes = models.TextField(blank=True)
    is_demo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["current_status"]),
            models.Index(fields=["patient_type"]),
            models.Index(fields=["department"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.patient_id})"

    @property
    def age(self):
        if not self.date_of_birth:
            return None
        today = date.today()
        years = today.year - self.date_of_birth.year
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            years -= 1
        return years

    @property
    def allergy_list(self):
        return [item.strip() for item in self.allergies.split(",") if item.strip()]


class Vitals(models.Model):
    """Point-in-time observations recorded by nursing staff."""

    class Status(models.TextChoices):
        NORMAL = "normal", "Normal"
        ABNORMAL = "abnormal", "Abnormal"
        CRITICAL = "critical", "Critical"

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="vitals")
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="vitals_recorded",
    )
    recorded_at = models.DateTimeField()
    temperature_c = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    pulse_bpm = models.PositiveIntegerField(null=True, blank=True)
    respiratory_rate = models.PositiveIntegerField(null=True, blank=True)
    bp_systolic = models.PositiveIntegerField(null=True, blank=True)
    bp_diastolic = models.PositiveIntegerField(null=True, blank=True)
    spo2 = models.PositiveIntegerField(null=True, blank=True)
    blood_glucose = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    pain_score = models.PositiveSmallIntegerField(null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NORMAL)
    notes = models.CharField(max_length=250, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-recorded_at"]
        verbose_name_plural = "Vitals"

    def __str__(self):
        return f"Vitals for {self.patient.name} at {self.recorded_at:%Y-%m-%d %H:%M}"

    @property
    def blood_pressure(self):
        if self.bp_systolic and self.bp_diastolic:
            return f"{self.bp_systolic}/{self.bp_diastolic}"
        return None


class NurseAssignment(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        HANDED_OVER = "handed_over", "Handed Over"

    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="nurse_assignments"
    )
    nurse = models.ForeignKey(
        "staff.Staff", on_delete=models.CASCADE, related_name="patient_assignments"
    )
    shift = models.ForeignKey(
        "staff.Shift", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    assigned_on = models.DateField(default=date.today)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    notes = models.CharField(max_length=250, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-assigned_on"]

    def __str__(self):
        return f"{self.nurse.name} -> {self.patient.name} ({self.assigned_on})"
