"""
Role based and object level permissions.

Every API view declares the ``module`` it belongs to (for example
``module = "patients"``).  :class:`ModulePermission` then maps the HTTP method
to an action and checks the caller's role matrix.  Object level scoping is
implemented by ``ScopedQuerysetMixin`` in ``users/scoping.py``.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import RoleCode

ACTION_BY_METHOD = {
    "GET": "view",
    "HEAD": "view",
    "OPTIONS": "view",
    "POST": "create",
    "PUT": "edit",
    "PATCH": "edit",
    "DELETE": "delete",
}

# Custom @action endpoints act on an existing record (dispense, approve,
# assign, record_payment...), so they require "edit" rather than "create".
STANDARD_ACTIONS = {
    "list",
    "create",
    "retrieve",
    "update",
    "partial_update",
    "destroy",
}


class IsAuthenticatedAndActive(BasePermission):
    """Default permission: any authenticated, active user."""

    message = "Your session has expired. Please log in again."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_active)


class ModulePermission(IsAuthenticatedAndActive):
    """
    Module aware permission.

    Views may override ``get_required_action`` for custom endpoints such as
    ``@action(detail=True, methods=["post"])``.
    """

    message = "You do not have permission to perform this action."

    def get_module(self, request, view):
        return getattr(view, "module", None)

    def get_required_action(self, request, view):
        override = getattr(view, "action", None)
        if override and hasattr(view, "action_permissions"):
            mapped = getattr(view, "action_permissions", {}).get(override)
            if mapped:
                return mapped
        if override and override not in STANDARD_ACTIONS:
            return "view" if request.method in SAFE_METHODS else "edit"
        return ACTION_BY_METHOD.get(request.method, "view")

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        module = self.get_module(request, view)
        if module is None:
            return True

        user = request.user
        if user.is_superuser or user.role == RoleCode.SUPER_ADMIN:
            return True

        action = self.get_required_action(request, view)
        if request.method in SAFE_METHODS and request.method != "GET":
            action = "view"
        return user.has_module_permission(module, action)


class IsAdministrator(BasePermission):
    message = "Only administrators can perform this action."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_administrator)


class IsAdministratorOrReadOnly(BasePermission):
    message = "Only administrators can modify hospital settings."

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated and user.is_active):
            return False
        return request.method in SAFE_METHODS or user.is_administrator
