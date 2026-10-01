"""Conversation storage for the hospital assistant and document assistant."""

from django.conf import settings
from django.db import models


class ChatSession(models.Model):
    class Mode(models.TextChoices):
        HOSPITAL = "hospital", "Hospital Assistant"
        DOCUMENT = "document", "Document Assistant"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chat_sessions"
    )
    mode = models.CharField(max_length=20, choices=Mode.choices, default=Mode.HOSPITAL)
    title = models.CharField(max_length=160, blank=True)
    patient = models.ForeignKey(
        "patients.Patient",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="chat_sessions",
    )
    provider = models.CharField(max_length=30, default="demo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title or f"Session {self.pk}"


class ChatMessage(models.Model):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
        SYSTEM = "system", "System"

    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=12, choices=Role.choices)
    content = models.TextField()
    sources = models.JSONField(
        default=list, blank=True, help_text="Document references backing the answer."
    )
    data_snapshot = models.JSONField(default=dict, blank=True)
    provider = models.CharField(max_length=30, default="demo")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.content[:60]}"
