"""Immutable record of who did what, when, and to which object."""

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """
    One row per meaningful action.

    ``username``/``role`` are denormalised snapshots so the trail stays readable
    even if the account is later renamed or removed.  No clinical payload is
    stored here - only a short description and the affected object reference.
    """

    SEVERITY = [
        ("info", "Info"),
        ("warning", "Warning"),
        ("critical", "Critical"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    username = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=60, blank=True)
    action = models.CharField(max_length=120)
    module = models.CharField(max_length=60, db_index=True)
    severity = models.CharField(max_length=20, choices=SEVERITY, default="info")
    object_type = models.CharField(max_length=80, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    method = models.CharField(max_length=10, blank=True)
    path = models.CharField(max_length=300, blank=True)
    status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["module", "-created_at"]),
            models.Index(fields=["object_type", "object_id"]),
        ]
        verbose_name = "Audit log entry"

    def __str__(self):
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {self.username}: {self.description or self.action}"
