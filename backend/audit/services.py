"""Helper used by every module to write audit entries."""

import logging

from . import context
from .models import AuditLog

logger = logging.getLogger(__name__)


def log_action(
    action,
    module,
    user=None,
    obj=None,
    description="",
    request=None,
    severity="info",
    **extra,
):
    """
    Record an audit entry.

    Never raises: an audit failure must not break the user's request.
    """
    request = request or context.get_current_request()
    if user is None and request is not None:
        candidate = getattr(request, "user", None)
        if candidate is not None and getattr(candidate, "is_authenticated", False):
            user = candidate

    object_type = ""
    object_id = ""
    if obj is not None:
        object_type = obj.__class__.__name__
        object_id = str(getattr(obj, "pk", "") or "")

    try:
        entry = AuditLog.objects.create(
            user=user if getattr(user, "pk", None) else None,
            username=getattr(user, "username", "") or "",
            role=getattr(user, "role", "") or "",
            action=action,
            module=module,
            severity=severity,
            object_type=object_type,
            object_id=object_id,
            description=description,
            ip_address=context.client_ip(request),
            user_agent=(request.META.get("HTTP_USER_AGENT", "")[:300] if request else ""),
            method=(getattr(request, "method", "") or "") if request else "",
            path=((getattr(request, "path", "") or "")[:300] if request else ""),
            status_code=extra.get("status_code"),
        )
        context.mark_explicit_log()
        return entry
    except Exception:  # pragma: no cover - defensive
        logger.exception("Failed to write audit log entry for %s/%s", module, action)
        return None


MODULE_BY_PREFIX = {
    "patients": "patients",
    "doctors": "doctors",
    "appointments": "appointments",
    "opd": "opd",
    "emergency": "emergency",
    "admissions": "admissions",
    "beds": "beds",
    "laboratory": "laboratory",
    "radiology": "radiology",
    "pharmacy": "pharmacy",
    "surgery": "surgery",
    "blood-bank": "bloodbank",
    "documents": "documents",
    "ai": "ai",
    "billing": "billing",
    "insurance": "insurance",
    "inventory": "inventory",
    "staff": "staff",
    "notifications": "notifications",
    "analytics": "analytics",
    "audit": "audit",
    "users": "users",
    "departments": "departments",
    "hospital": "hospital",
    "navigation": "navigation",
}


def module_from_path(path):
    parts = [part for part in path.split("/") if part]
    if len(parts) >= 2 and parts[0] == "api":
        return MODULE_BY_PREFIX.get(parts[1], parts[1])
    return "system"
