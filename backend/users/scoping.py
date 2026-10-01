"""
Object level authorisation helpers.

Role matrices control *which modules* a user may touch.  These mixins control
*which rows* they may see, which is what stops (for example) a patient from
reading another patient's chart.
"""

from django.db.models import Q

from .models import RoleCode


class PatientScopedQuerysetMixin:
    """
    Restrict a queryset for users whose access is tied to a single patient.

    The view sets ``patient_lookup`` to the ORM path leading from the model to
    :class:`patients.models.Patient` (``"patient"``, ``"admission__patient"``).
    """

    patient_lookup = "patient"

    def scope_queryset(self, queryset):
        user = self.request.user
        if user.is_superuser or user.role in {RoleCode.SUPER_ADMIN, RoleCode.HOSPITAL_ADMIN}:
            return queryset

        if user.role == RoleCode.PATIENT:
            patient_id = getattr(getattr(user, "patient_profile", None), "pk", None)
            if patient_id is None:
                return queryset.none()
            # ``patient_lookup`` is "id" when the queryset *is* the patient table.
            lookup = "pk" if self.patient_lookup == "id" else f"{self.patient_lookup}_id"
            return queryset.filter(**{lookup: patient_id})

        if user.role in {RoleCode.DOCTOR, RoleCode.HOD}:
            doctor = getattr(user, "doctor_profile", None)
            if doctor is None:
                return queryset.none()
            return queryset.filter(
                Q(**{f"{self.patient_lookup}__assigned_doctor": doctor})
                | Q(**{f"{self.patient_lookup}__admissions__doctor": doctor})
                | Q(**{f"{self.patient_lookup}__opd_visits__doctor": doctor})
                | Q(**{f"{self.patient_lookup}__appointments__doctor": doctor})
            ).distinct()

        if user.role == RoleCode.NURSE:
            nurse = getattr(user, "staff_profile", None)
            department = getattr(user, "department", None)
            filters = Q()
            if department is not None:
                filters |= Q(**{f"{self.patient_lookup}__department": department})
            if nurse is not None:
                filters |= Q(**{f"{self.patient_lookup}__nurse_assignments__nurse": nurse})
            if not filters:
                return queryset.none()
            return queryset.filter(filters).distinct()

        if user.role in {RoleCode.LAB_TECHNICIAN, RoleCode.RADIOLOGIST, RoleCode.PHARMACIST}:
            return queryset

        if user.role in {RoleCode.BILLING_STAFF, RoleCode.INSURANCE_STAFF}:
            return queryset

        return queryset
