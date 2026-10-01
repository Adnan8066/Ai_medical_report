# Shared base viewsets.
#
# Every module viewset inherits from these so that permission checks, object
# level scoping and audit logging are applied consistently instead of being
# re-implemented twenty times.

from rest_framework import viewsets

from audit.services import log_action
from users.permissions import ModulePermission
from users.scoping import PatientScopedQuerysetMixin


class BaseViewSet(viewsets.ModelViewSet):
    """CRUD viewset with module permissions, scoping and audit logging."""

    module = None
    permission_classes = [ModulePermission]
    apply_patient_scope = False
    patient_lookup = "patient"

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.apply_patient_scope:
            queryset = PatientScopedQuerysetMixin.scope_queryset(self, queryset)
        return queryset

    def _audit(self, verb, instance):
        log_action(
            action=f"{verb} {instance.__class__.__name__}",
            module=self.module or "system",
            obj=instance,
            description=f"{verb} {instance}.",
        )

    def perform_create(self, serializer):
        instance = serializer.save()
        self._audit("Created", instance)
        return instance

    def perform_update(self, serializer):
        instance = serializer.save()
        self._audit("Updated", instance)
        return instance

    def perform_destroy(self, instance):
        self._audit("Deleted", instance)
        instance.delete()


class BaseReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    """Read only viewset with module permissions and patient scoping."""

    module = None
    permission_classes = [ModulePermission]
    apply_patient_scope = False
    patient_lookup = "patient"

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.apply_patient_scope:
            queryset = PatientScopedQuerysetMixin.scope_queryset(self, queryset)
        return queryset
