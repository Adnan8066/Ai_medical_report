"""User, role and permission models for the platform's RBAC layer."""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class RoleCode(models.TextChoices):
    """The 13 roles described in the project brief."""

    SUPER_ADMIN = "super_admin", "Super Admin"
    HOSPITAL_ADMIN = "hospital_admin", "Hospital Admin"
    HOD = "hod", "Head of Department"
    DOCTOR = "doctor", "Doctor"
    NURSE = "nurse", "Nurse"
    RECEPTIONIST = "receptionist", "Receptionist"
    LAB_TECHNICIAN = "lab_technician", "Laboratory Technician"
    RADIOLOGIST = "radiologist", "Radiologist"
    PHARMACIST = "pharmacist", "Pharmacist"
    BILLING_STAFF = "billing_staff", "Billing Staff"
    INSURANCE_STAFF = "insurance_staff", "Insurance Staff"
    INVENTORY_MANAGER = "inventory_manager", "Inventory Manager"
    PATIENT = "patient", "Patient"


ADMIN_ROLES = {RoleCode.SUPER_ADMIN, RoleCode.HOSPITAL_ADMIN}

CLINICAL_ROLES = {
    RoleCode.HOD,
    RoleCode.DOCTOR,
    RoleCode.NURSE,
    RoleCode.LAB_TECHNICIAN,
    RoleCode.RADIOLOGIST,
    RoleCode.PHARMACIST,
}


class Role(models.Model):
    """
    A configurable role.

    ``permissions`` is a JSON matrix of the shape::

        {"patients": ["view", "create"], "billing": ["view"]}

    The defaults live in :mod:`users.roles` and are written to the database by
    the ``seed_demo_data`` management command, which lets an administrator
    adjust role capabilities from the UI without a code change.
    """

    code = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=80)
    description = models.TextField(blank=True)
    is_system = models.BooleanField(
        default=False, help_text="System roles cannot be deleted."
    )
    permissions = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def allows(self, module, action):
        return action in (self.permissions or {}).get(module, [])


class User(AbstractUser):
    """Custom user model - email is the login identifier."""

    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=40, choices=RoleCode.choices, default=RoleCode.RECEPTIONIST
    )
    employee_id = models.CharField(max_length=30, unique=True, null=True, blank=True)
    phone = models.CharField(max_length=25, blank=True)
    department = models.ForeignKey(
        "hospital.Department",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users",
    )
    designation = models.CharField(max_length=120, blank=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    is_demo = models.BooleanField(
        default=False, help_text="Marks accounts that ship with the demo dataset."
    )
    last_seen = models.DateTimeField(null=True, blank=True)

    REQUIRED_FIELDS = ["email"]
    USERNAME_FIELD = "username"

    _permission_cache = None

    class Meta:
        ordering = ["first_name", "last_name", "username"]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    # -- convenience -------------------------------------------------------

    @property
    def full_name(self):
        return self.get_full_name() or self.username

    @property
    def role_name(self):
        return self.get_role_display()

    @property
    def is_super_admin(self):
        return self.role == RoleCode.SUPER_ADMIN or self.is_superuser

    @property
    def is_administrator(self):
        return self.role in ADMIN_ROLES or self.is_superuser

    @property
    def is_clinical(self):
        return self.role in CLINICAL_ROLES

    @property
    def is_patient(self):
        return self.role == RoleCode.PATIENT

    def permission_matrix(self):
        if self._permission_cache is None:
            role = Role.objects.filter(code=self.role).first()
            if role is None:
                from .roles import DEFAULT_ROLE_PERMISSIONS

                self._permission_cache = dict(DEFAULT_ROLE_PERMISSIONS.get(self.role, {}))
            else:
                self._permission_cache = dict(role.permissions or {})
        return self._permission_cache

    def has_module_permission(self, module, action="view"):
        if not self.is_active:
            return False
        if self.is_superuser or self.role == RoleCode.SUPER_ADMIN:
            return True
        matrix = self.permission_matrix()
        if "*" in matrix.get(module, []):
            return True
        return action in matrix.get(module, [])

    def touch(self):
        self.last_seen = timezone.now()
        self.save(update_fields=["last_seen"])
