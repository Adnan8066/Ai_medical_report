"""In-application notifications with read tracking."""

from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Level(models.TextChoices):
        INFO = "info", "Info"
        SUCCESS = "success", "Success"
        WARNING = "warning", "Warning"
        CRITICAL = "critical", "Critical"

    class Category(models.TextChoices):
        APPOINTMENT = "appointment", "Appointment"
        LABORATORY = "laboratory", "Laboratory"
        RADIOLOGY = "radiology", "Radiology"
        PHARMACY = "pharmacy", "Pharmacy"
        BED = "bed", "Bed Management"
        BILLING = "billing", "Billing"
        INSURANCE = "insurance", "Insurance"
        ADMISSION = "admission", "Admission"
        DISCHARGE = "discharge", "Discharge"
        INVENTORY = "inventory", "Inventory"
        DOCUMENT = "document", "Documents"
        AI = "ai", "AI Assistant"
        SYSTEM = "system", "System"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="notifications",
        help_text="Leave empty to broadcast to all authorised staff.",
    )
    role_target = models.CharField(
        max_length=40, blank=True, help_text="Optional role code for broadcast messages."
    )
    title = models.CharField(max_length=160)
    message = models.CharField(max_length=300)
    category = models.CharField(
        max_length=20, choices=Category.choices, default=Category.SYSTEM
    )
    level = models.CharField(max_length=20, choices=Level.choices, default=Level.INFO)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    link = models.CharField(max_length=200, blank=True)
    is_demo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["is_read", "-created_at"])]

    def __str__(self):
        return self.title
