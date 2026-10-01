"""Insurance providers, patient policies and claims."""

from django.db import models


class InsuranceProvider(models.Model):
    name = models.CharField(max_length=140, unique=True)
    code = models.CharField(max_length=20, unique=True)
    contact_person = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=250, blank=True)
    claim_portal = models.CharField(max_length=150, blank=True)
    is_demo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class InsurancePolicy(models.Model):
    class PolicyType(models.TextChoices):
        INDIVIDUAL = "individual", "Individual Health"
        FAMILY = "family", "Family Floater"
        CORPORATE = "corporate", "Corporate Group"
        GOVERNMENT = "government", "Government Scheme"
        CRITICAL_ILLNESS = "critical_illness", "Critical Illness"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"

    policy_number = models.CharField(max_length=60, unique=True)
    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="insurance_policies"
    )
    provider = models.ForeignKey(
        InsuranceProvider, on_delete=models.PROTECT, related_name="policies"
    )
    policy_type = models.CharField(
        max_length=25, choices=PolicyType.choices, default=PolicyType.INDIVIDUAL
    )
    coverage_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valid_from = models.DateField()
    valid_to = models.DateField()
    corporate_account = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    is_demo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-valid_to"]
        verbose_name_plural = "Insurance policies"

    def __str__(self):
        return f"{self.policy_number} - {self.patient.name}"


class InsuranceClaim(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under Review"
        APPROVED = "approved", "Approved"
        PARTIALLY_APPROVED = "partially_approved", "Partially Approved"
        REJECTED = "rejected", "Rejected"
        SETTLED = "settled", "Settled"

    claim_number = models.CharField(max_length=30, unique=True)
    policy = models.ForeignKey(
        InsurancePolicy, on_delete=models.PROTECT, related_name="claims"
    )
    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="insurance_claims"
    )
    invoice = models.ForeignKey(
        "billing.Invoice",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="insurance_claims",
    )
    claim_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    approved_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    rejected_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.SUBMITTED)
    submitted_date = models.DateField()
    reviewed_date = models.DateField(null=True, blank=True)
    settled_date = models.DateField(null=True, blank=True)
    diagnosis_code = models.CharField(max_length=20, blank=True)
    treatment_summary = models.CharField(max_length=300, blank=True)
    rejection_reason = models.CharField(max_length=250, blank=True)
    notes = models.TextField(blank=True)
    handled_by = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="claims_handled",
    )
    is_demo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-submitted_date"]
        indexes = [models.Index(fields=["status"])]

    def __str__(self):
        return f"{self.claim_number} - {self.patient.name}"
