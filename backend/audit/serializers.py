from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            "id",
            "username",
            "role",
            "action",
            "module",
            "severity",
            "object_type",
            "object_id",
            "description",
            "ip_address",
            "method",
            "path",
            "status_code",
            "created_at",
        ]
        read_only_fields = fields
